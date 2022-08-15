#
#  Copyright (c) 2021 International Business Machines
#  All rights reserved.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  Authors: anita.shekar@ibm.com, sandy.kaur@ibm.com
#

import ctypes
import ctypes.util
import os
import shlex
import sys
import signal
import socket
import subprocess
import grpc
import json
import logging
from concurrent import futures
from .proto import gateway_pb2_grpc as pb2_grpc
from .config import OmapPersistentConfig
from .grpc import GatewayService

libc = ctypes.CDLL(ctypes.util.find_library("c"))
PR_SET_PDEATHSIG = 1


def set_pdeathsig(sig=signal.SIGTERM):

    def callable():
        return libc.prctl(PR_SET_PDEATHSIG, sig)

    return callable


class GatewayServer:
    """Runs SPDK and receives client requests for the gateway service.

    Instance attributes:
        settings: Basic gateway parameters
        logger: Logger instance to track server events
        gateway_name: Gateway identifier
        gateway_rpc: GatewayService object on which to make RPC calls directly
        server: gRPC server instance to receive gateway client requests
        persistent_config: Methods for target configuration persistence
        spdk_rpc: Module methods for SPDK
        spdk_rpc_client: Client of SPDK RPC server
        spdk_rpc_ping_client: Ping client of SPDK RPC server
        spdk_process: Subprocess running SPDK NVMEoF target application
    """

    def __init__(self, settings):

        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.spdk_process = None
        self.server = None
        self.spdk_process = None
        self.server = None

        self.gateway_name = self.settings.get("gateway", "name")
        if not self.gateway_name:
            self.gateway_name = socket.gethostname()
        self.logger.info(f"Starting gateway {self.gateway_name}")

        self._start_spdk()
        self.persistent_config = OmapPersistentConfig(self.settings)
        self.gateway_rpc = GatewayService(self.settings, self.persistent_config,
                                          self.spdk_rpc, self.spdk_rpc_client)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Cleans up SPDK and server instances."""

        if self.spdk_process is not None:
            self.logger.info("Terminating SPDK...")
            self.spdk_process.terminate()
            try:
                timeout = self.settings.getfloat("spdk", "timeout")
                self.spdk_process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.spdk_process.kill()

        if self.server is not None:
            self.logger.info("Stopping the server...")
            self.server.stop(None)

        self.logger.info("Exiting the gateway process.")
        return True

    def _start_spdk(self):
        """Starts SPDK process."""

        # Get path and import SPDK's RPC modules
        spdk_path = self.settings.get("spdk", "spdk_path")
        sys.path.append(spdk_path)
        self.logger.info(f"SPDK PATH: {spdk_path}")
        import spdk.scripts.rpc as spdk_rpc
        self.spdk_rpc = spdk_rpc

        # Start target
        tgt_path = self.settings.get("spdk", "tgt_path")
        spdk_rpc_socket = self.settings.get("spdk", "rpc_socket")
        spdk_tgt_cmd_extra_args = self.settings.get("spdk",
                                                       "tgt_cmd_extra_args")
        spdk_cmd = os.path.join(spdk_path, tgt_path)
        cmd = [spdk_cmd, "-u", "-r", spdk_rpc_socket]
        if spdk_tgt_cmd_extra_args:
            cmd += shlex.split(spdk_tgt_cmd_extra_args)
        self.logger.info(f"Starting {' '.join(cmd)}")
        try:
            self.spdk_process = subprocess.Popen(cmd,
                                                 preexec_fn=set_pdeathsig(
                                                     signal.SIGTERM))
        except Exception as ex:
            self.logger.error(f"Unable to start SPDK: \n {ex}")
            raise

        # Initialization
        timeout = self.settings.getfloat("spdk", "timeout")
        log_level = self.settings.get("spdk", "log_level")
        conn_retries = self.settings.getint("spdk", "conn_retries")
        self.logger.info({
            f"Attempting to initialize SPDK: rpc_socket: {spdk_rpc_socket},",
            f" conn_retries: {conn_retries}, timeout: {timeout}",
        })
        try:
            self.spdk_rpc_client = self.spdk_rpc.client.JSONRPCClient(
                spdk_rpc_socket,
                None,
                timeout,
                log_level=log_level,
                conn_retries=conn_retries,
            )
            self.spdk_rpc_ping_client = self.spdk_rpc.client.JSONRPCClient(
                spdk_rpc_socket,
                None,
                timeout,
                log_level=log_level,
                conn_retries=conn_retries,
            )
        except Exception as ex:
            self.logger.error(f"Unable to initialize SPDK: \n {ex}")
            raise

        # Implicity create transports
        spdk_transports = self.settings.get_with_default(
            "spdk", "transports", "tcp")
        for trtype in spdk_transports.split():
            self._create_transport(trtype.lower())

    def _create_transport(self, trtype):
        """Initializes a transport type."""
        args = {'trtype': trtype}
        name = "transport_" + trtype + "_options"
        options = self.settings.get_with_default("spdk", name, "")

        self.logger.debug(f"create_transport: {trtype} options: {options}")

        if options:
            try:
                args.update(json.loads(options))
            except json.decoder.JSONDecodeError as ex:
                self.logger.error(
                    f"Failed to parse spdk {name} ({options}): \n {ex}")
                raise

        try:
            status = self.spdk_rpc.nvmf.nvmf_create_transport(
                self.spdk_rpc_client, **args)
        except Exception as ex:
            self.logger.error(
                f"Create Transport {trtype} returned with error: \n {ex}")
            raise

    def serve(self):
        """Starts up server."""

        # Register service implementation with server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        pb2_grpc.add_NVMEGatewayServicer_to_server(
            self.gateway_rpc, self.server)

        enable_auth = self.settings.getboolean("gateway", "enable_auth")
        gateway_addr = self.settings.get("gateway", "addr")
        gateway_port = self.settings.get("gateway", "port")

        if enable_auth:
            # Read in key and certificates for authentication
            server_key = self.settings.get("mtls", "server_key")
            server_cert = self.settings.get("mtls", "server_cert")
            client_cert = self.settings.get("mtls", "client_cert")
            with open(server_key, "rb") as f:
                private_key = f.read()
            with open(server_cert, "rb") as f:
                server_crt = f.read()
            with open(client_cert, "rb") as f:
                client_crt = f.read()

            # Create appropriate server credentials
            server_credentials = grpc.ssl_server_credentials(
                private_key_certificate_chain_pairs=[
                    (private_key, server_crt)],
                root_certificates=client_crt,
                require_client_auth=True,
            )

            # Add secure port using crendentials
            self.server.add_secure_port(
                "{}:{}".format(gateway_addr, gateway_port), server_credentials)
        else:
            # Authentication is not enabled
            self.server.add_insecure_port("{}:{}".format(
                gateway_addr, gateway_port))

        # Check for existing NVMeoF target configuration
        self._restore_config()
        # Start server
        self.logger.info("Starting server")
        self.server.start()
        while True:
            timedout = self.server.wait_for_termination(timeout=1)
            if not timedout:
                break
            alive = self._ping()
            if not alive:
                break

    def _restore_config(self):
        """Restores NVMeoF target configuration."""

        callbacks = {
            self.persistent_config.BDEV_PREFIX: self.gateway_rpc.bdev_rbd_create,
            self.persistent_config.SUBSYSTEM_PREFIX: self.gateway_rpc.nvmf_create_subsystem,
            self.persistent_config.NAMESPACE_PREFIX: self.gateway_rpc.nvmf_subsystem_add_ns,
            self.persistent_config.HOST_PREFIX: self.gateway_rpc.nvmf_subsystem_add_host,
            self.persistent_config.LISTENER_PREFIX: self.gateway_rpc.nvmf_subsystem_add_listener
        }
        self.persistent_config.restore(callbacks)

    def _ping(self):
        """Confirms communication with SPDK process."""
        try:
            ret = self.spdk_rpc.spdk_get_version(self.spdk_rpc_ping_client)
            return True
        except Exception as ex:
            self.logger.error(f"spdk_get_version failed with: \n {ex}")
            return False
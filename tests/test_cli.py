import pytest
import socket
from control.cli import main as cli

image = "iscsidevimage"
pool = "rbd"
bdev = "Ceph0"
subsystem = "nqn.2016-06.io.spdk:cnode1"
serial = "SPDK00000000000001"
host_list = ["nqn.2016-06.io.spdk:host1", "*"]
nsid = "1"
trtype = "TCP"
gateway_name = socket.gethostname()
addr = "127.0.0.1"
listener_list = [["-g", gateway_name, "-a", addr, "-s", "5001"], ["-s", "5002"]]
settings = "main.settings"

class TestGet:
    def test_get_subsystems(self, caplog):
        cli(["-s", settings, "get_subsystems"])
        assert "Failed to get" not in caplog.text

class TestCreate:
    def test_create_bdev(self, caplog):
        cli(["-s", settings, "create_bdev", "-i", image, "-p", pool, "-b", bdev])
        assert "Failed to create" not in caplog.text

    def test_create_subsystem(self, caplog):
        cli(["-s", settings, "create_subsystem", "-n", subsystem, "-s", serial])
        assert "Failed to create" not in caplog.text

    def test_create_namespace(self, caplog):
        cli(["-s", settings, "create_namespace", "-n", subsystem, "-b", bdev])
        assert "Failed to add" not in caplog.text

    @pytest.mark.parametrize("host", host_list)
    def test_add_host(self, caplog, host):
        cli(["-s", settings, "add_host", "-n", subsystem, "-t", host])
        assert "Failed to add" not in caplog.text

    @pytest.mark.parametrize("listener", listener_list)
    def test_create_listener(self, caplog, listener):
        cli(["-s", settings, "create_listener", "-n", subsystem] + listener)
        assert "Failed to create" not in caplog.text

class TestDelete:
    @pytest.mark.parametrize("host", host_list)
    def test_delete_host(self, caplog, host):
        cli(["-s", settings, "delete_host", "-n", subsystem, "-t", host])
        assert "Failed to remove" not in caplog.text

    @pytest.mark.parametrize("listener", listener_list)
    def test_delete_listener(self, caplog, listener):
        cli(["-s", settings, "delete_listener", "-n", subsystem] + listener)
        assert "Failed to delete" not in caplog.text

    def test_delete_namespace(self, caplog):
        cli(["-s", settings, "delete_namespace", "-n", subsystem, "-i", nsid])
        assert "Failed to remove" not in caplog.text

    def test_delete_bdev(self, caplog):
        cli(["-s", settings, "delete_bdev", "-b", bdev])
        assert "Failed to delete" not in caplog.text

    def test_delete_subsystem(self, caplog):
        cli(["-s", settings, "delete_subsystem", "-n", subsystem])
        assert "Failed to delete" not in caplog.text

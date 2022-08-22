import unittest
from unittest import mock
from unittest.mock import Mock, MagicMock
from control.config import OmapPersistentConfig
from control.proto.gateway_pb2 import bdev_create_req
from control.proto.gateway_pb2 import subsystem_add_ns_req
from control.proto.gateway_pb2 import subsystem_create_req
from control.proto.gateway_pb2 import subsystem_add_host_req
from control.proto.gateway_pb2 import subsystem_add_listener_req
from google.protobuf import json_format
import rados
import pdb

class OmapPersistentConfigTester(unittest.TestCase):


    @mock.patch('control.config.rados')
    def test_init_pass(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = Mock()

        # Test succcess 
        mock_rados.Rados.return_value.open_ioctx.return_value.set_omap.return_value=Mock()
        omap = OmapPersistentConfig(settingsMock)
        assert omap.version == 1 

    @mock.patch('control.config.rados')
    def test_init_fail_1(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = Mock()

        omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.new.side_effect = Exception()

        with self.assertRaises(Exception):
            omap = OmapPersistentConfig(settingsMock)
       
    @mock.patch('control.config.rados')
    def test_init_fail_2(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = Mock()

        mock_rados.WriteOpCtx.side_effect = Exception()
        with self.assertRaises(Exception):
            omap = OmapPersistentConfig(settingsMock)
       
    @mock.patch('control.config.rados')
    def test_init_fail_3(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = Mock()

        # Reset mock and test exception 
        mock_rados.WriteOpCtx.side_effect = rados.ObjectExists()
        with self.assertRaises(rados.ObjectExists):
             omap = OmapPersistentConfig(settingsMock)
       
    @mock.patch('control.config.rados')
    def test_init_fail_4(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = Mock()

        # Test exception 
        mock_rados.Rados.return_value.open_ioctx.return_value.set_omap.side_effect = Exception()
        with self.assertRaises(Exception):
            omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.new.assert_called()
        
    @mock.patch('control.config.rados')
    def test_write_key_pass(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = "abc"

        # In debugger, print(write_op.omap_cmp.called) true in config.py
        mock_rados.WriteOpCtx.__enter__.return_value = Mock()
        mock_rados.WriteOpCtx.return_value.__enter__ = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap.ioctx = Mock()
        omap._write_key(Mock(),Mock())
        omap.ioctx.operate_write_op.assert_called_with(
                mock_rados.WriteOpCtx.return_value.__enter__.return_value, 'nvme.abc.config')
        assert omap.version == 2 
   
    @mock.patch('control.config.rados')
    def test_write_key_fail(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = "abc"
        omap = OmapPersistentConfig(settingsMock)

        mock_rados.WriteOpCtx.side_effect = Exception()
        with self.assertRaises(Exception):
            omap._write_key(Mock(),Mock())
        assert omap.version == 1 

    @mock.patch('control.config.rados')
    def test_delete_key_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap.ioctx = Mock()
        omap._delete_key("delete")
        assert omap.ioctx.set_omap.call_count == 1 
        assert omap.ioctx.remove_omap_keys.call_count == 1 
        assert omap.version == 2 

    @mock.patch('control.config.rados')
    def test_add_bdev_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._write_key= Mock()
        omap._write_key.return_value = True
        omap.add_bdev("test1", "test2")
        omap._write_key.assert_called_with("bdev_test1", "test2")
   
    @mock.patch('control.config.rados')
    def test_add_bdev_fail(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        # Test exception thrown  
        settingsMock.reset_mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._write_key= Mock()
        omap._write_key.side_effect = Exception()
        with self.assertRaises(Exception):
            omap.add_bdev("test1", "test2")

    @mock.patch('control.config.rados')
    def test_delete_bdev_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._delete_key= Mock()
        omap._delete_key.return_value = True
        omap.delete_bdev("test1")
        omap._delete_key.assert_called_with("bdev_test1")
   
    @mock.patch('control.config.rados')
    def test_delete_bdev_fail(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        
        omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.omap_cmp.side_effect = Exception()

        with self.assertRaises(Exception):
            omap.delete_bdev("test1")

    @mock.patch('control.config.rados')
    def test_restore_bdevs_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        callbackMock = Mock()
        val = '{"bdev_name": "bdev_1", "user_id": "user", "ceph_pool_name": "rbd_pool", "rbd_name": "name", "block_size": 1}'
        my_dict = {'bdev_1': val}
        omap._restore_bdevs(my_dict, callbackMock)
        req = json_format.Parse(val,bdev_create_req())
        callbackMock.assert_called_with(req)

    @mock.patch('control.config.rados')
    def test_add_namespace(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._write_key = Mock()
        omap.add_namespace("namespace", "nsid", "value")
        omap._write_key.assert_called_with("namespace_namespace_nsid", "value")

    @mock.patch('control.config.rados')
    def test_add_namespace(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.omap_cmp.side_effect = Exception()
        with self.assertRaises(Exception):
            omap.add_namespace("namespace", "nsid", "value")
    
    @mock.patch('control.config.rados')
    def test_delete_namespace_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._delete_key = Mock()
        omap.delete_namespace("namespace", "nsid")
        omap._delete_key.assert_called_with("namespace_namespace_nsid")

    @mock.patch('control.config.rados')
    def test_delete_namespace_fail(self, mock_rados):
        settingsMock = Mock()
        # Reset mock and test exception 
        omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.omap_cmp.side_effect = Exception()
        with self.assertRaises(Exception):
            omap.delete_namespace("namespace", "nsid")
            omap._delete_key.assert_called_with("namespace_namespace_nsid")

    @mock.patch('control.config.rados')
    def test_restore_namespace_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        callbackMock = Mock()
        val = '{"subsystem_nqn": "nqn", "bdev_name": "bdev_1"}'
        my_dict = {'namespace_1': val}
        omap._restore_namespaces(my_dict, callbackMock)
        req = json_format.Parse(val,subsystem_add_ns_req())
        req.nsid = 1
        callbackMock.assert_called_with(req)
    
    @mock.patch('control.config.rados')
    def test_add_subsystem_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._write_key = Mock()
        omap.add_subsystem("namespace", "nsid")
        omap._write_key.assert_called_with("subsystem_namespace", "nsid")

    @mock.patch('control.config.rados')
    def test_add_subsystem_fail(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        # Reset mock and test exception 
        
        omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.omap_cmp.side_effect = Exception()
        with self.assertRaises(Exception):
            omap.delete_subsystem("namespace", "nsid")
            omap._write_key.assert_called_with("subsystem_namespace", "nsid")

    @mock.patch('control.config.rados')
    def test_restore_subsystems_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        callbackMock = Mock()
        val = '{"subsystem_nqn": "nqn"}'
        my_dict = {'subsystem_1': val}
        omap._restore_subsystems(my_dict, callbackMock)
        req = json_format.Parse(val,subsystem_create_req())
        callbackMock.assert_called_with(req)
    
    @mock.patch('control.config.rados')
    def test_add_host_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._write_key = Mock()
        omap.add_host("subsystem", "host_nqn", "value")
        omap._write_key.assert_called_with("host_subsystem_host_nqn", "value")

    @mock.patch('control.config.rados')
    def test_add_host_fail(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        # Reset mock and test exception 
        
        omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.omap_cmp.side_effect = Exception()
        with self.assertRaises(Exception):
            omap.add_host("subsystem", "host_nqn", "value")
            omap._write_key.assert_called_with("host_subsystem_host_nqn", "value")

    @mock.patch('control.config.rados')
    def test_delete_host_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._delete_key = Mock()
        omap.delete_host("subsystem", "host_nqn")
        omap._delete_key.assert_called_with("host_subsystem_host_nqn")


    @mock.patch('control.config.rados')
    def test_restore_hosts_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        callbackMock = Mock()
        val = '{"subsystem_nqn": "nqn", "host_nqn": "host"}'
        my_dict = {'host_1': val}
        omap._restore_hosts(my_dict, callbackMock)
        req = json_format.Parse(val,subsystem_add_host_req())
        callbackMock.assert_called_with(req)

    @mock.patch('control.config.rados')
    def _test_add_listener(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._write_key = Mock()
        omap.add_listener("nqn", "gateway", "trtype", "traddr", "trsvcid", "val")
        omap._write_key.assert_called_with("listener_gateway_nqn_trtype_traddr_trsvcid", "val")

    @mock.patch('control.config.rados')
    def _test_add_listener(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        # Reset mock and test exception 
        
        omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.return_value.__enter__.return_value.omap_cmp.side_effect = Exception()
        with self.assertRaises(Exception):
            omap.add_listener("nqn", "gateway", "trtype", "traddr", "trsvcid", "val")
    
    
    @mock.patch('control.config.rados')
    def test_delete_listener(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._delete_key = Mock()
        omap.delete_listener("nqn", "gateway", "trtype", "traddr", "trsvcid")
        omap._delete_key.assert_called_with("listener_gateway_nqn_trtype_traddr_trsvcid")
    
    @mock.patch('control.config.rados')
    def test_restore_listeners_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        callbackMock = Mock()
        val = '{"nqn": "nqn_1", "gateway_name": "gtway", "trtype": "tr", "adrfam": "adrfam", "traddr": "traddr", "trsvcid": "123"}'
        my_dict = {'listener_name': val}
        omap._restore_listeners(my_dict, callbackMock)
        req = json_format.Parse(val,subsystem_add_listener_req())
        callbackMock.assert_called_with(req)

    @mock.patch('control.config.rados')
    def test_restore_listeners_fail(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        callbackMock = Mock()
        # Reset mock and test exception 
        callbackMock.reset_mock() 
        my_dict = {}
        omap._restore_listeners(my_dict, callbackMock)
        callbackMock.assert_not_called()
    
    @mock.patch('control.config.rados')
    def test_read_key_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap.ioctx.get_omap_vals_by_keys = Mock()
        omap.ioctx.get_omap_vals_by_keys.return_value = [{"myName": "v1", "test1":"v2"}, {"test3":"v3", "test4":"4"}]
        ret_value = omap._read_key("abc")
        assert ret_value == None
        my_bytes = 'v1'.encode('utf-8') 
        omap.ioctx.get_omap_vals_by_keys.return_value = [{"myName": my_bytes}, "test"]
        ret_value = omap._read_key("abc")
        assert ret_value == "v1"

    @mock.patch('control.config.rados')
    def test_read_all_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap.ioctx.get_omap_vals = Mock()
        omap.ioctx.get_omap_vals.return_value = [{"myName": "v1", "test1":"v2"}, {"test3":"v3", "test4":"4"}]
        ret_map = omap._read_all()
        assert ret_map == {"myName": "v1", "test1":"v2"}

    @mock.patch('control.config.rados')
    def test_delete_config_pass(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = "gateway_group"
        omap = OmapPersistentConfig(settingsMock)
        omap.delete_config()
        omap.ioctx.remove_object.assert_called_with("nvme.gateway_group.config")
  
    @mock.patch('control.config.rados')
    def test_delete_config_fail(self, mock_rados):
        settingsMock = Mock()
        # settingsMock.get.return_value = "gateway_group"
        # Reset mock and test exception 
        settingsMock.reset_mock()
        settingsMock.get.return_value = ""
        
        omap = OmapPersistentConfig(settingsMock)
        # The side effect is set to throwing exception 
        mock_rados.ObjectNotFound = rados.ObjectNotFound
        omap.ioctx.remove_object.side_effect = rados.ObjectNotFound()
        omap.delete_config()
        omap.ioctx.remove_object.assert_called_with("nvme.config")
    
    @mock.patch('control.config.rados')
    def test_restore_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        omap._read_key = Mock()
        omap._read_all = Mock()
        omap._read_key.return_value = "1"
        omap.restore(settingsMock)
        omap._read_all.assert_not_called()

        omap._read_key.return_value = "2"
        omap._read_all = Mock()
        mydict = {'omap_version': "2"}
        omap._read_all.return_value = mydict
        omap._restore_bdevs = Mock()
        omap._restore_subsystems = Mock()
        omap._restore_namespaces = Mock()
        omap._restore_hosts = Mock()
        omap._restore_listeners = Mock()
        callback = {
            omap.BDEV_PREFIX: Mock(),
            omap.SUBSYSTEM_PREFIX: Mock(),
            omap.NAMESPACE_PREFIX: Mock(),
            omap.HOST_PREFIX: Mock(),
            omap.LISTENER_PREFIX: Mock()
        }
        omap.restore(callback)
        omap._restore_bdevs.assert_called_with(mydict, callback[omap.BDEV_PREFIX])
        omap._restore_subsystems.assert_called_with(mydict, callback[omap.SUBSYSTEM_PREFIX])
        omap._restore_namespaces.assert_called_with(mydict, callback[omap.NAMESPACE_PREFIX])
        omap._restore_hosts.assert_called_with(mydict, callback[omap.HOST_PREFIX])
        omap._restore_listeners.assert_called_with(mydict, callback[omap.LISTENER_PREFIX])
        omap._restore_listeners.assert_called_with(mydict, callback[omap.LISTENER_PREFIX])
        assert omap.version == int("2")

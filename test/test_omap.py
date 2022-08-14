import unittest
from unittest import mock
from unittest.mock import Mock, MagicMock
from control.config import OmapPersistentConfig
import rados
import pdb

class OmapPersistentConfigTester(unittest.TestCase):

## TODO:
# pdb calls
# print(mock_rados.WriteOpCtx.__dict__)
# print(mock_rados.__dict__)
# print(mock_rados._mock_children['WriteOpCtx'].__dict__)
    @mock.patch('control.config.rados')
    def test_write_key_pass(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = "abc"

        # In debugger, print(write_op.omap_cmp.called) true in config.py
        mock_rados.WriteOpCtx.__enter__.return_value = Mock()
        # mock_rados.WriteOpCtx.return_value.omap_comp = Mock()
        omap = OmapPersistentConfig(settingsMock)
        # Now we can do something like print(omap.ioctx.operate_write_op.called) and know that function 
        # was called
        omap.ioctx = Mock()
        omap._write_key(Mock(),Mock())
        # Assert that the operate_write_op was called once 
        assert omap.ioctx.operate_write_op.call_count == 1 
        # Tuple iteration
        # for calls in mock_rados.mock_calls:
        #      for call in calls: 
        #          args = call
        #          print("inner")
        #          print(call)
        #      print("outer")
        for call in omap.ioctx.operate_write_op.call_args_list:
             args, kwargs = call
             # assert first artument to operate_write_op is a Mock object
             # for reference assert isinstance(args[0], MagicMock)
             # assert 2nd argument to operate_write_op is the omap_name
             assert args[1] == 'nvme.abc.config'
       
        assert omap.version == 2 
    
    @mock.patch('control.config.rados')
    def test_write_key_fail(self, mock_rados):
        settingsMock = Mock()
        # mock_rados.Rados.return_value.open_ioctx.return_value.set_omap.return_value=Mock()
        omap = OmapPersistentConfig(settingsMock)
        mock_rados.WriteOpCtx.side_effect = Exception()
        with self.assertRaises(Exception):
            omap._write_key(Mock(),Mock())
        assert omap.version == 1 

    @mock.patch('control.config.rados')
    def test_init_with_pass(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = Mock()
        mock_rados.Rados.return_value.open_ioctx.return_value.set_omap.return_value=Mock()

        omap = OmapPersistentConfig(settingsMock)
        assert omap.version == 1 

    @mock.patch('control.config.rados')
    def test_init_fail_1(self, mock_rados):
        settingsMock = Mock()
        settingsMock.get.return_value = Mock()
        mock_rados.Rados.return_value.open_ioctx.return_value.set_omap.side_effect = Exception()

        # mock_ioctx.set_omap.return_value = True
        with self.assertRaises(Exception):
            omap = OmapPersistentConfig(settingsMock)
        
    @mock.patch('control.config.rados')
    def test_init_with_fail_2(self, mock_rados):
        mockObj = Mock()
        mockObj.get.return_value = Mock()
        mock_rados.Rados.return_value = Mock() 
         
        mock_rados.WriteOpCtx.side_effect = Exception()
        with self.assertRaises(Exception):
            omap = OmapPersistentConfig(mockObj)
        
        mock_rados.WriteOpCtx.side_effect = rados.ObjectExists()
        with self.assertRaises(rados.ObjectExists):
             omap = OmapPersistentConfig(mockObj)

        with mock.patch.object(mockObj, "ioctx.set_omap") as mock_ioctx:
            # mock_ioctx.set_omap.side_effect = Exception()
            mock_ioctx.set_omap.return_value = True
            with self.assertRaises(Exception):
                omap = OmapPersistentConfig(mockObj)
        
        #try: 
        #    omap = OmapPersistentConfig(mockObj)
        #except rados.ObjectExists as e:
        #    pass
        #except Exception as ex:
        #    assert False
            
        # self.post_patch = mock.patch('requests.post')
    
    @mock.patch('control.config.rados')
    def test_delete_key_pass(self, mock_rados):
        settingsMock = Mock()
        omap = OmapPersistentConfig(settingsMock)
        # mock_rados.WriteOpCtx.side_effect = Exception()
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
        # mock_rados.return_value.WriteOpCtx.__enter__.return_value = Mock()
        # mock_rados.return_value.WriteOpCtx.__enter__.side_effect = Exception()
        # mock_rados.WriteOpCtx.set_omap.side_effect = Exception()
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
        # mock_rados.return_value.WriteOpCtx.__enter__.return_value = Mock()
        # mock_rados.return_value.WriteOpCtx.__enter__.side_effect = Exception()
        # mock_rados.WriteOpCtx.set_omap.side_effect = Exception()
        omap = OmapPersistentConfig(settingsMock)
        omap._delete_key= Mock()
        omap._delete_key.side_effect = Exception()
        with self.assertRaises(Exception):
            omap.delete_bdev("test1")

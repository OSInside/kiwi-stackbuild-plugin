from kiwi_stackbuild_plugin.defaults import StackBuildDefaults


class TestDefaults:
    def test_is_container_name_valid(self):
        assert StackBuildDefaults.is_container_name_valid(
            'foo'
        ) is True
        assert StackBuildDefaults.is_container_name_valid(
            'Leap-15.3_appliance'
        ) is False

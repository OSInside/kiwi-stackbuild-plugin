import shutil
from pytest import raises
from tempfile import mkdtemp
from mock import patch

from kiwi.exceptions import (
    KiwiConfigFileNotFound
)

from kiwi_stackbuild_plugin.xml_merge import XMLMerge
from kiwi_stackbuild_plugin.exceptions import (
    KiwiStackBuildPluginSchemaValidationFailed
)


class TestXMLMerge:
    def setup(self):
        self.target_dir = mkdtemp(prefix='kiwi_desc_target.')

    def setup_method(self, cls):
        self.setup()

    def teardown_method(self, cls):
        shutil.rmtree(self.target_dir)

    def test_XMLMerge_no_description(self):
        with raises(KiwiConfigFileNotFound):
            XMLMerge(self.target_dir)

    def test_is_stackbuild_description(self):
        xml_merge = XMLMerge('../data/stackbuild-description')
        assert xml_merge.is_stackbuild_description()

    def test_is_not_stackbuild_description(self):
        xml_merge = XMLMerge('../data/kiwi-description')
        assert not xml_merge.is_stackbuild_description()

    def test_validate_schema(self):
        xml_merge = XMLMerge('../data/stackbuild-description')
        xml_merge.validate_schema()

    def test_validate_schema_fails(self):
        xml_merge = XMLMerge('../data/kiwi-description')
        with raises(KiwiStackBuildPluginSchemaValidationFailed):
            xml_merge.validate_schema()

    @patch('kiwi_stackbuild_plugin.xml_merge.DataSync')
    def test_merge_description(self, mock_DataSync):
        shutil.copy('../data/kiwi-description/config.xml', self.target_dir)
        xml_merge = XMLMerge('../data/stackbuild-description')
        xml_merge.validate_schema()
        xml_merge.merge_description('../data/kiwi-description', self.target_dir)

    @patch('kiwi_stackbuild_plugin.xml_merge.DataSync')
    def test_merge_description_without_profiles(self, mock_DataSync):
        shutil.copy('../data/kiwi-description/alternate-config.kiwi', self.target_dir)
        xml_merge = XMLMerge('../data/stackbuild-description')
        xml_merge.validate_schema()
        xml_merge.merge_description('../data/kiwi-description', self.target_dir)

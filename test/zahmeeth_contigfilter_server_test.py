import unittest
import os
import json
import time

from os import environ
from ConfigParser import ConfigParser
from pprint import pprint

from biokbase.workspace.client import Workspace as workspaceService
from zahmeeth_contigfilter.zahmeeth_contigfilterImpl import zahmeeth_contigfilter


class zahmeeth_contigfilterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        cls.ctx = {'token': token, 'provenance': [{'service': 'zahmeeth_contigfilter',
            'method': 'please_never_use_it_in_production', 'method_params': []}],
            'authenticated': 1}
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('zahmeeth_contigfilter'):
            cls.cfg[nameval[0]] = nameval[1]
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL, token=token)
        cls.serviceImpl = zahmeeth_contigfilter(cls.cfg)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_zahmeeth_contigfilter_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def test_filter_contigs_ok(self):
        obj_name = "contigset.1"
        contig1 = {'id': '1', 'length': 10, 'md5': 'md5', 'sequence': 'agcttttcat'}
        contig2 = {'id': '2', 'length': 5, 'md5': 'md5', 'sequence': 'agctt'}
        contig3 = {'id': '3', 'length': 12, 'md5': 'md5', 'sequence': 'agcttttcatgg'}
        obj1 = {'contigs': [contig1, contig2, contig3], 'id': 'id', 'md5': 'md5', 'name': 'name', 
                'source': 'source', 'source_id': 'source_id', 'type': 'type'}
        self.getWsClient().save_objects({'workspace': self.getWsName(), 'objects':
            [{'type': 'KBaseGenomes.ContigSet', 'name': obj_name, 'data': obj1}]})
        ret = self.getImpl().filter_contigs(self.getContext(), {'workspace': self.getWsName(), 
            'contigset_id': obj_name, 'min_length': '10'})
        obj2 = self.getWsClient().get_objects([{'ref': self.getWsName()+'/'+obj_name}])[0]['data']
        self.assertEqual(len(obj2['contigs']), 2)
        self.assertTrue(len(obj2['contigs'][0]['sequence']) >= 10)
        self.assertTrue(len(obj2['contigs'][1]['sequence']) >= 10)
        self.assertEqual(ret[0]['n_initial_contigs'], 3)
        self.assertEqual(ret[0]['n_contigs_removed'], 1)
        self.assertEqual(ret[0]['n_contigs_remaining'], 2)

    def test_filter_contigs_err1(self):
        with self.assertRaises(ValueError) as context:
            self.getImpl().filter_contigs(self.getContext(), {'workspace': self.getWsName(), 
                'contigset_id': 'fake', 'min_length': 10})
        self.assertTrue('Error loading original ContigSet object' in str(context.exception))

    def test_filter_contigs_err2(self):
        with self.assertRaises(ValueError) as context:
            self.getImpl().filter_contigs(self.getContext(), {'workspace': self.getWsName(), 
                'contigset_id': 'fake', 'min_length': '-10'})
        self.assertTrue('min_length parameter shouldn\'t be negative' in str(context.exception))

    def test_filter_contigs_err3(self):
        with self.assertRaises(ValueError) as context:
            self.getImpl().filter_contigs(self.getContext(), {'workspace': self.getWsName(), 
                'contigset_id': 'fake', 'min_length': 'ten'})
        self.assertTrue('Cannot parse integer from min_length parameter' in str(context.exception))
        
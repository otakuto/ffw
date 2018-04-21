import unittest
import os

from common.networkdata import NetworkData
from honggmode.honggcorpusdata import HonggCorpusData
from honggmode.honggcorpusmanager import HonggCorpusManager


class HonggCorpusManagerTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "inputs": "/tmp/ffw-test/in/",
            "temp": "/tmp/ffw-test/temp/"
        }
        return config


    def _getNetworkData(self, config):
        networkMessages = [
            {
                'data': 'msg 1 cli',
                'from': 'cli',
                'index': 0,
            },
            {
                'data': 'msg 2 srv',
                'from': 'srv',
                'index': 1,
            }
        ]

        networkData = NetworkData(config,
                                  networkMessages)
        return networkData


    def _getCorpusData(self, config):
        networkData = self._getNetworkData(config)
        corpusData = HonggCorpusData(config, 'data0', networkData)
        return corpusData


    def _prepareFs(self, config):
        if not os.path.exists(config["temp"]):
            os.makedirs(config["temp"])

        if not os.path.exists(config["inputs"]):
            os.makedirs(config["inputs"])
        else:
            for the_file in os.listdir(config["inputs"]):
                file_path = os.path.join(config["inputs"], the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    #elif os.path.isdir(file_path): shutil.rmtree(file_path)
                except Exception as e:
                    print(e)


    def test_loadfiles(self):
        """Test if we can load the initial corpus."""
        config = self._getConfig()
        self._prepareFs(config)

        # write an corpus file
        corpusData = self._getCorpusData(config)
        corpusData.writeToFile()

        # load all corpus files
        honggCorpusManager = HonggCorpusManager(config)
        honggCorpusManager.loadCorpusFiles()
        self.assertEqual(honggCorpusManager.getCorpusCount(), 1)


    def test_getNotified(self):
        """Check if we get notified (and can load) new files."""
        config = self._getConfig()
        self._prepareFs(config)

        # load all corpus - should be empty
        honggCorpusManager = HonggCorpusManager(config)
        honggCorpusManager.loadCorpusFiles()
        self.assertEqual(honggCorpusManager.getCorpusCount(), 0)

        # start it up
        honggCorpusManager.startWatch()

        # write file
        corpusData = self._getCorpusData(config)
        corpusData.seed = 42
        corpusData.writeToFile()

        # check if we detect the file write
        honggCorpusManager.checkForNewFiles()
        self.assertEqual(honggCorpusManager.getCorpusCount(), 1)

        # some more sanity checks
        corpusData = honggCorpusManager.corpus[0]
        self.assertNotEqual(corpusData.seed, None)
        self.assertTrue(corpusData.isExternal)
        self.assertFalse(corpusData.processed)


    def test_doCreate(self):
        """Test if wo correctly add new corpus we found ourselfs."""
        config = self._getConfig()
        self._prepareFs(config)

        # load all corpus - should be empty
        honggCorpusManager = HonggCorpusManager(config)
        honggCorpusManager.loadCorpusFiles()
        self.assertEqual(honggCorpusManager.getCorpusCount(), 0)

        # start it up
        honggCorpusManager.startWatch()

        # imitate fuzzer which has been detected new corpus
        # we add it here, but it should not generate a notification
        # (because we already have it, but still watching for files)
        corpusData = self._getCorpusData(config)
        corpusData.seed = 42
        honggCorpusManager.addNewCorpusData(corpusData)

        self.assertEqual(honggCorpusManager.getCorpusCount(), 1)
        honggCorpusManager.checkForNewFiles()
        # should be still 1
        self.assertEqual(honggCorpusManager.getCorpusCount(), 1)

        corpusData = honggCorpusManager.corpus[0]
        self.assertFalse(corpusData.isExternal)
        self.assertTrue(corpusData.processed)


if __name__ == '__main__':
    unittest.main()

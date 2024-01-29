import os
import urllib.request as request
from zipfile import ZipFile
from tqdm import tqdm
from pathlib import Path

from deepClassifier.entity import DataIngestionConfig
from deepClassifier import logger
from deepClassifier.utils import get_size


class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config

    def download_file(self):
        logger.info("Trying to download file...")
        if not os.path.exists(self.config.local_data_file):  # data file doesn't exists
            logger.info("Download started...")
            with tqdm(unit="B", unit_scale=True, miniters=1, desc="Downloading") as t:

                def hook(t):
                    def inner(chunk, chunk_size, remote_size):
                        t.update(chunk_size)

                    return inner

                filename, headers = request.urlretrieve(
                    url=self.config.source_URL,
                    filename=self.config.local_data_file,
                    reporthook=hook(t),
                )
            logger.info(f"{filename} download! with following info: \n{headers}")
        else:
            logger.info(
                f"File already exists of size: {get_size(Path(self.config.local_data_file))}"
            )

    def _get_updated_list_of_files(self, list_of_files):
        """
        To remove unnecessary files inside the data, like Thumbs.db
        """
        return [
            f
            for f in list_of_files
            if f.endswith(".jpg") and ("Cat" in f or "Dog" in f)
        ]

    def _preprocess(self, zf: ZipFile, f: str, working_dir: str):
        """
        Preprocess data. Remove files with zero size.
        """
        target_filepath = os.path.join(working_dir, f)
        if not os.path.exists(target_filepath):
            zf.extract(f, working_dir)

        if os.path.getsize(target_filepath) == 0:
            logger.info(
                f"removing file:{target_filepath} of size: {get_size(Path(target_filepath))}"
            )
            os.remove(target_filepath)

    def unzip_and_clean(self):
        logger.info("unzipping file and removing unawanted files")
        with ZipFile(file=self.config.local_data_file, mode="r") as zf:
            list_of_files = zf.namelist()
            updated_list_of_files = self._get_updated_list_of_files(list_of_files)
            for f in tqdm(updated_list_of_files):
                self._preprocess(zf, f, self.config.unzip_dir)

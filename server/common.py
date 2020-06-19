import configparser
import argparse
import logging
import logging.config
import yaml
import math
import traceback
from uvicorn.logging import AccessFormatter, DefaultFormatter
from tensorflow.keras.models import load_model as load_keras_model
from fasttext import load_model as load_fasttext_model

config = None
fasttext_model = None
toxicity_model = None


def init_config(override_args=None):
    global config
    parser = argparse.ArgumentParser(description='ComEx web server')
    parser.add_argument('--config', type=str, default='configs/example.ini',
                        help='Path to the config file to use')
    args = parser.parse_args(override_args)

    config = configparser.ConfigParser()
    # init config with defaults
    config.read('configs/DEFAULT.ini')
    # override with user defined config
    config.read(args.config)


def get_logger_config() -> dict:
    with open(config.get('logging', 'config_file'), 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)


def init_logging(logger_name: str = None):
    logging.config.dictConfig(get_logger_config())
    if logger_name:
        return logging.getLogger(logger_name)


class AccessLogFormatter(AccessFormatter):
    def formatMessage(self, record):
        try:
            record.__dict__.update({
                'wall_time': record.__dict__['scope']['timing_stats']['wall_time'],
                'cpu_time': record.__dict__['scope']['timing_stats']['cpu_time']
            })
        except KeyError:
            record.__dict__.update({
                'wall_time': '0.0?s',
                'cpu_time': '0.0?s'
            })
        return super().formatMessage(record)


class ColourFormatter(DefaultFormatter):
    def formatMessage(self, record):
        pad = (8 - len(record.levelname)) / 2
        levelname = ' ' * math.ceil(pad) + record.levelname + ' ' * math.floor(pad)
        if self.use_colors:
            record.__dict__['levelnamec'] = self.color_level_name(levelname, record.levelno)
        else:
            record.__dict__['levelnamec'] = levelname

        return super().formatMessage(record)


def except2str(e, logger=None):
    if config.getboolean('server', 'debug_mode'):
        tb = traceback.format_exc()
        if logger:
            logger.error(tb)
        return tb
    return f'{type(e).__name__}: {e}'


def init_or_get_fasttext_model():
    global fasttext_model
    if fasttext_model is None:
        fasttext_model = load_fasttext_model(config.get('TextProcessing', 'fasttext_path'))
    return fasttext_model


def init_or_get_toxicity_model():
    global toxicity_model
    if toxicity_model is None:
        toxicity_model = load_keras_model(config.get('TextProcessing', 'toxicity_path'))
    return toxicity_model


__all__ = ['get_logger_config', 'config', 'init_logging', 'init_config', 'except2str', 'init_or_get_fasttext_model',
           'init_or_get_toxicity_model']

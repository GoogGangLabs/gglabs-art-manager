from blender_validator.model import StdoutLogger

# TODO: Consider to make an independent logging module.
# NOTE: python `logging` doesn't work with blender, AFAICS
logger = StdoutLogger()

__all__ = ["logger"]

import traitlets.config as tlc
from collections import OrderedDict
import traitlets as tl

class AstroSingleton:
    config_classes = []

    def __init__(self, **kwargs ):
        self.config_classes.append( self.__class__ )

    @classmethod
    def generate_config_file( cls ):
        """generate default config file from Configurables"""
        lines = ['']
 #       cfg_classes = cls.config_classes
        cfg_classes = list( cls._classes_with_config_traits())
 #       print( f"generate_config_file, classes = {cls.config_classes} {cfg_classes}")
        for clss in cfg_classes:
            lines.append( clss.class_config_section(cfg_classes) )
        return '\n'.join(lines)

    @classmethod
    def _classes_inc_parents(cls):
        """Iterate through configurable classes, including configurable parents """
        seen = set()
        for c in cls.config_classes:
            # We want to sort parents before children, so we reverse the MRO
            for parent in reversed(c.mro()):
                if issubclass(parent, tlc.Configurable) and (parent not in seen):
                    seen.add(parent)
                    yield parent

    @classmethod
    def _classes_with_config_traits(cls):
        """ Yields only classes with configurable traits, and their subclasses.  """
        cls_to_config = OrderedDict( (cls, bool(cls.class_own_traits(config=True))) for cls in cls._classes_inc_parents())

        def is_any_parent_included(cls):
            return any(b in cls_to_config and cls_to_config[b] for b in cls.__bases__)

        ## Mark "empty" classes for inclusion if their parents own-traits, and loop until no more classes gets marked.
        while True:
            to_incl_orig = cls_to_config.copy()
            cls_to_config = OrderedDict( (cls, inc_yes or is_any_parent_included(cls)) for cls, inc_yes in cls_to_config.items())
            if cls_to_config == to_incl_orig:
                break
        for cl, inc_yes in cls_to_config.items():
            if inc_yes:
                yield cl
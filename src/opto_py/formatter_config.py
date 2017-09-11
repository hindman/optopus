from .enums import HelpTextStyle, OptTextStyle

class FormatterConfig(object):

    DEFAULTS = dict(
        program_name        = '',
        section_label_punct = ':',
        after_section_label = '',
        after_section       = '\n',
        program_summary     = '',
        style               = HelpTextStyle.CLI,
        opt_style           = OptTextStyle.CLI,
    )

    def __init__(self, *sections, **kws):
        self.sections = sections
        for k, v in self.DEFAULTS.items():
            val = kws.get(k, v)
            setattr(self, k, val)

class Section(object):

    def __init__(self, name, label, text = None, opts = None):
        self.name = name
        self.label = label
        self.text = text
        self.opts = opts

        # TODO: validation: require either text or opts, and not both.


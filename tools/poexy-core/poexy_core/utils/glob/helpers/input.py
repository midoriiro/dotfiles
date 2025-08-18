from poexy_core.utils.glob.helpers.slice import SliceView


class Input(SliceView):
    def __init__(self, _input: str) -> None:
        super().__init__(base=_input, start=0, end=len(_input))

from pathlib import Path

import finesse

from finorch.sessions.abstract_wrapper import AbstractWrapper


class CITWrapper(AbstractWrapper):
    def run(self):
        katscript = open('script.k', 'r').read()

        kat = finesse.Model()
        kat.parse(katscript)
        out = kat.run()
        finesse.save(out, Path.cwd() / "data.pickle")

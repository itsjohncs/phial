# internal
import phial.pipelines
import phial.utils


class TestDocuments:
    def test_concat(self):
        files = [phial.utils.TemporaryFile("a"), phial.utils.TemporaryFile("b")]
        for i, f in enumerate(files):
            f.write(str(i))

        source = phial.pipelines.PipelineSource(files)
        source.pipe(phial.pipelines.concat("joined"))

        assert len(source.contents) == 1
        assert source.contents[0].read() == "".join(str(i) for i in range(len(files)))
        assert source.contents[0].name == "joined"

    def test_exec(self):
        files = [phial.utils.TemporaryFile("a"), phial.utils.TemporaryFile("b")]
        for i, f in enumerate(files):
            f.write(str(i))

        source = phial.pipelines.PipelineSource(files)
        source.pipe(phial.pipelines.run("joined", ["cat"]))

        assert len(source.contents) == 1
        assert source.contents[0].read() == "".join(str(i) for i in range(len(files)))
        assert source.contents[0].name == "joined"

# internal
import phial.pipelines
import phial.utils


class TestPipeline:
    def test_concat(self):
        files = [phial.documents.file("a"), phial.documents.file("b")]
        for i, f in enumerate(files):
            f.write(str(i))

        source = phial.pipelines.PipelineSource(files)
        source.pipe(phial.pipelines.concat("joined"))

        assert len(source.contents) == 1
        assert source.contents[0].read() == "".join(str(i) for i in range(len(files)))
        assert source.contents[0].name == "joined"

    def test_exec(self):
        files = [phial.documents.file("a"), phial.documents.file("b")]
        for i, f in enumerate(files):
            f.write(str(i))

        source = phial.pipelines.PipelineSource(files)
        source.pipe(phial.pipelines.run("joined", ["cat"]))

        assert len(source.contents) == 1
        assert source.contents[0].read() == "".join(str(i) for i in range(len(files)))
        assert source.contents[0].name == "joined"

    def test_interface(self):
        files = [phial.documents.file("a"), phial.documents.file("b")]
        for i, f in enumerate(files):
            f.write(str(i))

        source = phial.pipelines.PipelineSource(files)
        result = source | phial.pipelines.concat("joined")

        assert len(result.contents) == 1
        assert result.contents[0].read() == "".join(str(i) for i in range(len(files)))
        assert result.contents[0].name == "joined"

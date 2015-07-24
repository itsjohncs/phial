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

    def test_map(self):
        def transform(f):
            # Seek to the end of the file and add a 1
            f.seek(0, 2)
            f.write("1")
            return f

        files = [phial.documents.file("a", content="a"), phial.documents.file("b", content="b")]
        result = phial.pipelines.PipelineSource(files) | phial.pipelines.map(transform)

        assert len(result.contents) == 2
        assert result.contents[0].read() == "a1"
        assert result.contents[1].read() == "b1"

    def test_map_counter(self):
        expected_contents = ["a", "b"]
        counter = {"_scope_hack": 0}

        def transform(f, index):
            assert index == counter["_scope_hack"]
            counter["_scope_hack"] += 1
            assert f.read() == expected_contents[index]
            return f

        files = [
            phial.documents.file("a", content=expected_contents[0]),
            phial.documents.file("b", content=expected_contents[1])
        ]
        phial.pipelines.PipelineSource(files) | phial.pipelines.map(transform, counter=True)
        assert counter["_scope_hack"] == 2

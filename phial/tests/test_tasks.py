# internal
import phial.tasks

# external
import pytest


Task = phial.tasks.Task
VALID_TASK_LISTS = {
    "no_dependencies": [
        Task(id=1),
        Task(id=2),
        Task(id=3),
    ],
    "simple_dependencies": [
        Task(id=3, depends_on=2),
        Task(id=1),
        Task(id=2, depends_on=1),
    ],
}


class TestTasks:
    @pytest.mark.parametrize("tasks", VALID_TASK_LISTS.values(), ids=VALID_TASK_LISTS.keys())
    def test_topological_sort(self, tasks):
        queue = phial.tasks.TaskQueue()
        for i in tasks:
            queue.enqueue(i)

        ids = [i.id for i in queue]
        print ids
        assert ids == sorted(ids)

    def test_topological_sort_cycle(self):
        tasks = [
            Task(id=1, depends_on=2),
            Task(id=2, depends_on=1),
        ]

        queue = phial.tasks.TaskQueue()
        for i in tasks:
            queue.enqueue(i)

        with pytest.raises(RuntimeError):
            iter(queue)

"""Unit tests for gherkins.StageManager."""

import pytest
from gherkins.StageManager import StageManager


def test_stage_decorator_registers_stage():
    sm = StageManager()

    @sm.stage("My Stage")
    def my_stage():
        pass

    assert len(sm.stages) == 1
    func, name = sm.stages[0]
    assert name == "My Stage"
    assert func is my_stage


def test_multiple_stages_registered_in_order():
    sm = StageManager()
    order = []

    @sm.stage("First")
    def first():
        order.append("First")

    @sm.stage("Second")
    def second():
        order.append("Second")

    @sm.stage("Third")
    def third():
        order.append("Third")

    assert [name for _, name in sm.stages] == ["First", "Second", "Third"]


def test_run_executes_all_stages_in_order():
    sm = StageManager()
    order = []

    @sm.stage("A")
    def a():
        order.append("A")

    @sm.stage("B")
    def b():
        order.append("B")

    @sm.stage("C")
    def c():
        order.append("C")

    sm.run()
    assert order == ["A", "B", "C"]


def test_run_with_stage_subset():
    sm = StageManager()
    order = []

    @sm.stage("Alpha")
    def alpha():
        order.append("Alpha")

    @sm.stage("Beta")
    def beta():
        order.append("Beta")

    @sm.stage("Gamma")
    def gamma():
        order.append("Gamma")

    sm.run(["Gamma", "Alpha"])
    assert order == ["Gamma", "Alpha"]


def test_run_unknown_stage_raises_value_error():
    sm = StageManager()

    @sm.stage("Existing")
    def existing():
        pass

    with pytest.raises(ValueError, match="Unknown stage"):
        sm.run(["Nonexistent"])


def test_run_unknown_stage_lists_available_stages():
    sm = StageManager()

    @sm.stage("Real Stage")
    def real():
        pass

    with pytest.raises(ValueError, match="Real Stage"):
        sm.run(["Fake Stage"])


def test_decorator_returns_original_function():
    """The decorator should not wrap the function — it must be callable directly."""
    sm = StageManager()
    result = []

    @sm.stage("Side Effect")
    def side_effect():
        result.append(1)

    side_effect()  # call directly, bypassing the pipeline
    assert result == [1]


def test_run_empty_pipeline():
    """Running with no registered stages should not raise."""
    sm = StageManager()
    sm.run()  # should complete without error


def test_run_empty_stages_list():
    """Passing an empty list to run() should execute nothing."""
    sm = StageManager()
    order = []

    @sm.stage("Step")
    def step():
        order.append("Step")

    sm.run([])
    assert order == []

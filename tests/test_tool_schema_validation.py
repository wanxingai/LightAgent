import json

import pytest

from LightAgent import LightAgent, ToolRegistry


def make_tool(name="search_database", description="Search records.", params=None):
    def tool(**kwargs):
        return kwargs

    tool.tool_info = {
        "tool_name": name,
        "tool_description": description,
        "tool_params": params if params is not None else [
            {
                "name": "query",
                "type": "string",
                "description": "Search query.",
                "required": True,
            }
        ],
    }
    return tool


def test_valid_tool_info_has_no_diagnostics():
    tool = make_tool()

    assert ToolRegistry.validate_tool_info(tool.tool_info) == []


def test_tool_info_validation_reports_schema_problems_without_mutation():
    tool_info = {
        "tool_name": "unsafe/tool",
        "tool_description": "",
        "tool_params": [
            {"name": "query", "type": "string", "description": "", "required": "yes"},
            {"name": "query", "type": "path", "required": False},
            "invalid",
        ],
    }
    original = {
        "tool_name": tool_info["tool_name"],
        "tool_description": tool_info["tool_description"],
        "tool_params": [dict(tool_info["tool_params"][0]), dict(tool_info["tool_params"][1]), "invalid"],
    }

    diagnostics = ToolRegistry.validate_tool_info(tool_info)

    assert tool_info == original
    assert {item["field"] for item in diagnostics} >= {
        "tool_name",
        "tool_description",
        "tool_params[0].description",
        "tool_params[0].required",
        "tool_params[1].name",
        "tool_params[1].type",
        "tool_params[1].description",
        "tool_params[2]",
    }
    assert all(set(item) == {"tool", "level", "field", "message"} for item in diagnostics)


def test_tool_info_validation_requires_dictionary_and_parameter_list():
    assert ToolRegistry.validate_tool_info(None)[0]["field"] == "tool_info"

    diagnostics = ToolRegistry.validate_tool_info({
        "tool_name": "valid_name",
        "tool_description": "Valid description.",
        "tool_params": {},
    })

    assert diagnostics == [{
        "tool": "valid_name",
        "level": "error",
        "field": "tool_params",
        "message": "tool_params must be a list",
    }]


def test_registry_reports_duplicate_tool_names_without_changing_overwrite_behavior():
    registry = ToolRegistry()
    first = make_tool(description="First implementation.")
    second = make_tool(description="Second implementation.")

    assert registry.register_tool(first) is True
    assert registry.register_tool(second) is True
    assert registry.function_mappings["search_database"] is second

    diagnostics = registry.validate_tools()

    duplicate = next(item for item in diagnostics if "registered 2 times" in item["message"])
    assert duplicate["level"] == "error"
    assert duplicate["field"] == "tool_name"


def test_registry_does_not_report_same_function_registered_again():
    registry = ToolRegistry()
    tool = make_tool()

    registry.register_tool(tool)
    registry.register_tool(tool)

    assert registry.validate_tools() == []


def _make_filterable_registry():
    registry = ToolRegistry()
    registry.register_tool(make_tool(name="search_database"))
    registry.register_tool(make_tool(name="get_weather"))
    return registry


def test_filter_tools_accepts_plain_json():
    registry = _make_filterable_registry()

    result = registry.filter_tools("{\"tools\": [{\"name\": \"get_weather\"}]}")

    names = [s["function"]["name"] for s in result]
    assert names == ["get_weather"]


def test_filter_tools_accepts_json_fenced_markdown_block():
    registry = _make_filterable_registry()

    result = registry.filter_tools('```json\n{"tools": [{"name": "search_database"}]}\n```')

    names = [s["function"]["name"] for s in result]
    assert names == ["search_database"]


def test_filter_tools_accepts_unlabeled_markdown_code_block():
    """LLMs frequently wrap JSON in a plain ``` fence without the `json` tag."""
    registry = _make_filterable_registry()

    result = registry.filter_tools('```\n{"tools": [{"name": "get_weather"}]}\n```')

    names = [s["function"]["name"] for s in result]
    assert names == ["get_weather"]


def test_filter_tools_accepts_fence_with_surrounding_prose():
    registry = _make_filterable_registry()

    result = registry.filter_tools(
        'Here are the tools I need:\n```json\n{"tools": [{"name": "search_database"}]}\n```'
    )

    names = [s["function"]["name"] for s in result]
    assert names == ["search_database"]


def test_filter_tools_accepts_json_embedded_in_prose_without_fence():
    registry = _make_filterable_registry()

    result = registry.filter_tools(
        "I need the weather. {\"tools\": [{\"name\": \"get_weather\"}]} Let me fetch it."
    )

    names = [s["function"]["name"] for s in result]
    assert names == ["get_weather"]


def test_filter_tools_still_reports_truly_invalid_content():
    registry = _make_filterable_registry()

    with pytest.raises(ValueError):
        registry.filter_tools("this is not json at all")


def test_filter_tools_reports_invalid_content_inside_a_fence():
    registry = _make_filterable_registry()

    with pytest.raises(ValueError):
        registry.filter_tools("```\nthis is not json either\n```")


def test_filter_tools_preserves_valid_json_with_fences_inside_strings():
    payload = {"tools": [{"name": "get_weather"}], "note": "```json {} ```"}
    result = _make_filterable_registry().filter_tools(json.dumps(payload))
    assert [item["function"]["name"] for item in result] == ["get_weather"]


@pytest.mark.parametrize("prefix", ["Context {}. Selection: ", "Context {not JSON}. Selection: "])
def test_filter_tools_skips_unrelated_braces_before_selection(prefix):
    text = prefix + json.dumps({"tools": [{"name": "get_weather"}], "note": 'quoted } brace and "text"'})
    result = _make_filterable_registry().filter_tools(text + " Done.")
    assert [item["function"]["name"] for item in result] == ["get_weather"]


def test_filter_tools_skips_invalid_first_fence():
    text = '```\nnot JSON\n```\n```json\n{"tools":[{"name":"get_weather"}]}\n```'
    result = _make_filterable_registry().filter_tools(text)
    assert [item["function"]["name"] for item in result] == ["get_weather"]


def test_filter_tools_rejects_conflicting_selections():
    text = '{"tools":[{"name":"get_weather"}]} or {"tools":[{"name":"search_database"}]}'
    with pytest.raises(ValueError, match="Conflicting tool selections"):
        _make_filterable_registry().filter_tools(text)


def test_filter_tools_accepts_repeated_equivalent_selections():
    text = '{"tools":[{"name":" GET_WEATHER "}]} again {"tools":[{"name":"get_weather"}]}'
    result = _make_filterable_registry().filter_tools(text)
    assert [item["function"]["name"] for item in result] == ["get_weather"]


@pytest.mark.parametrize("payload", [{}, {"tools": []}])
def test_filter_tools_preserves_empty_selection_compatibility(payload):
    assert _make_filterable_registry().filter_tools(json.dumps(payload)) == []


@pytest.mark.parametrize("payload", [[], {"tools": None}, {"tools": {}}, {"tools": [None]},
                                      {"tools": [{}]}, {"tools": [{"name": 42}]}])
def test_filter_tools_reports_invalid_selection_shapes(payload):
    with pytest.raises(ValueError):
        _make_filterable_registry().filter_tools(json.dumps(payload))


def test_filter_tools_cannot_add_unregistered_names():
    assert _make_filterable_registry().filter_tools('{"tools":[{"name":"unregistered"}]}') == []


def test_lightagent_exposes_registered_tool_diagnostics():
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        tools=[make_tool(description="")],
    )

    diagnostics = agent.validate_tools()

    assert any(item["field"] == "tool_description" for item in diagnostics)

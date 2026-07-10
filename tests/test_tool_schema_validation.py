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

"""Security regression tests for the execute_python_code blocklist.

CWE-184: Ensures the AST-based blocklist in _safe_import_check covers
both direct Name calls and Attribute calls for eval/exec/compile.
"""

from LightAgent.builtin_tools.python_executor import _safe_import_check


class TestSafeImportCheckBlocklist:
    """The AST blocklist must catch dangerous functions regardless
    of whether they are called as Name (eval(...)) or as Attribute
    (builtins.eval(...))."""

    # --- Direct Name calls (existing coverage) ---

    def test_blocks_direct_eval(self):
        safe, msg = _safe_import_check("eval('1+1')")
        assert not safe
        assert "eval" in msg

    def test_blocks_direct_exec(self):
        safe, msg = _safe_import_check("exec('x=1')")
        assert not safe
        assert "exec" in msg

    def test_blocks_direct_compile(self):
        safe, msg = _safe_import_check("compile('x=1','','exec')")
        assert not safe
        assert "compile" in msg

    def test_blocks_direct___import__(self):
        safe, msg = _safe_import_check("__import__('os')")
        assert not safe
        assert "__import__" in msg

    # --- Import-based access (existing coverage) ---

    def test_blocks_import_os(self):
        safe, msg = _safe_import_check("import os")
        assert not safe
        assert "os" in msg

    def test_blocks_import_subprocess(self):
        safe, msg = _safe_import_check("import subprocess")
        assert not safe
        assert "subprocess" in msg

    def test_blocks_from_builtins_import_eval(self):
        safe, msg = _safe_import_check("from builtins import eval")
        assert not safe
        assert "eval" in msg

    # --- Attribute calls — these are the regression tests ---
    # Prior to the fix, builtins.eval(...) bypassed the blocklist
    # because ast.Attribute.attr was not checked for 'eval'/'exec'.

    def test_blocks_attribute_eval(self):
        """builtins.eval(...) must be blocked."""
        safe, msg = _safe_import_check(
            "import builtins\n"
            "builtins.eval(\"__import__('os').system('id')\")"
        )
        assert not safe, "builtins.eval should be blocked"
        assert "eval" in msg or "危险函数" in msg or "禁止" in msg

    def test_blocks_attribute_exec(self):
        """builtins.exec(...) must be blocked."""
        safe, msg = _safe_import_check(
            "import builtins\n"
            "builtins.exec('x=1')"
        )
        assert not safe, "builtins.exec should be blocked"
        assert "exec" in msg or "危险函数" in msg or "禁止" in msg

    def test_blocks_attribute_compile(self):
        """builtins.compile(...) must be blocked."""
        safe, msg = _safe_import_check(
            "import builtins\n"
            "builtins.compile('x=1','','exec')"
        )
        assert not safe, "builtins.compile should be blocked"

    def test_blocks_nested_builtins_eval(self):
        """getattr(__builtins__, ...) eval bypass must also be blocked
        at the os.system() call level."""
        safe, msg = _safe_import_check(
            'getattr(__builtins__, "__import__")("os").system("id")'
        )
        assert not safe
        # The system() call should be caught
        assert "system" in msg or "子进程" in msg or "危险" in msg

    # --- Safe operations that MUST still pass ---

    def test_allows_harmless_computation(self):
        safe, msg = _safe_import_check("result = sum([1, 2, 3])")
        assert safe, f"Harmless code should pass: {msg}"

    def test_allows_print(self):
        safe, msg = _safe_import_check("print('hello world')")
        assert safe, f"print should pass: {msg}"

    def test_allows_len_and_range(self):
        safe, msg = _safe_import_check("items = list(range(10))\ncount = len(items)")
        assert safe, f"len/range should pass: {msg}"

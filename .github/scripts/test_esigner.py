import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("esigner", Path(__file__).with_name("esigner.py"))
esigner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(esigner)


class SigningTests(unittest.TestCase):
    def test_password_characters_are_preserved_without_logging(self):
        password = ' test%PATH%&x!^"quoted"$`value` '
        with tempfile.TemporaryDirectory() as temp:
            jar = Path(temp) / "adm-esigner-1.3.0/jar/code_sign_tool-1.3.0.jar"
            jar.parent.mkdir(parents=True)
            jar.touch()
            env = {"RUNNER_TEMP": temp, "JAVA_HOME": temp, "ES_USERNAME": "user",
                   "ES_PASSWORD": password, "CREDENTIAL_ID": "credential"}

            def run(args, **kwargs):
                self.assertFalse(kwargs["shell"])
                self.assertIn("-password=" + password, args)
                self.assertEqual(args[4], "get_credential_ids")
                return subprocess.CompletedProcess(args, 0, "Credential ID(s):\n- credential", "")

            output = io.StringIO()
            with patch.dict(os.environ, env), patch.object(esigner.sys, "argv", ["esigner.py"]), \
                    patch.object(esigner.subprocess, "run", side_effect=run), contextlib.redirect_stdout(output):
                esigner.main()
            self.assertNotIn(password, output.getvalue())
            self.assertIn("comprobados", output.getvalue())

    def test_invalid_grant_is_failure_even_with_zero_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            jar = Path(temp) / "adm-esigner-1.3.0/jar/code_sign_tool-1.3.0.jar"
            jar.parent.mkdir(parents=True)
            jar.touch()
            env = {"RUNNER_TEMP": temp, "JAVA_HOME": temp, "ES_USERNAME": "user",
                   "ES_PASSWORD": "private-value", "CREDENTIAL_ID": "credential"}
            result = subprocess.CompletedProcess([], 0, "Error: invalid_grant private-value", "")
            with patch.dict(os.environ, env), patch.object(esigner.sys, "argv", ["esigner.py"]), \
                    patch.object(esigner.subprocess, "run", return_value=result):
                with self.assertRaisesRegex(RuntimeError, "SSL.com rechazo el acceso") as error:
                    esigner.main()
            self.assertNotIn("private-value", str(error.exception))


if __name__ == "__main__":
    unittest.main()

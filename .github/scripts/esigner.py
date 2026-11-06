"""Run eSigner without passing credentials through cmd.exe or printing them."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile


URL = "https://github.com/SSLcom/CodeSignTool/releases/download/v1.3.0/CodeSignTool-v1.3.0-windows.zip"
SHA256 = "e22094505decbe622afe5b0c27abc618ed2ba179bd94f3450490352399d5ef2a"


def main():
    info = len(sys.argv) == 2 and sys.argv[1] == "--info"
    signing = len(sys.argv) == 2 and not info
    names = ["ES_USERNAME", "ES_PASSWORD", "CREDENTIAL_ID"]
    if signing:
        names.append("ES_TOTP_SECRET")
    if any(not os.environ.get(name) for name in names):
        raise RuntimeError("Faltan secretos de eSigner.")

    root = Path(os.environ["RUNNER_TEMP"]) / "adm-esigner-1.3.0"
    jar = root / "jar" / "code_sign_tool-1.3.0.jar"
    if not jar.exists():
        archive = root.with_suffix(".zip")
        urllib.request.urlretrieve(URL, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
            raise RuntimeError("La descarga de CodeSignTool no coincide con su SHA-256.")
        root.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as source:
            source.extractall(root)
        archive.unlink()

    java_home = os.environ.get("JAVA_HOME_11_X64") or os.environ.get("JAVA_HOME")
    java = Path(java_home) / "bin" / "java.exe" if java_home else root / "jdk-11.0.2/bin/java.exe"
    command = "sign" if signing else "credential_info" if info else "get_credential_ids"
    args = [str(java), "-Xmx1024M", "-jar", str(jar), command,
            "-username=" + os.environ["ES_USERNAME"],
            "-password=" + os.environ["ES_PASSWORD"]]
    if signing or info:
        args.append("-credential_id=" + os.environ["CREDENTIAL_ID"])
    if signing:
        args += ["-totp_secret=" + os.environ["ES_TOTP_SECRET"],
                 "-input_file_path=" + str(Path(sys.argv[1]).resolve()),
                 "-override=true", "-malware_block=false"]

    env = dict(os.environ, CODE_SIGN_TOOL_PATH=str(root))
    try:
        # A list and shell=False preserve quotes, %, &, and other password characters.
        result = subprocess.run(args, env=env, cwd=root, shell=False, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=180)
        output = result.stdout + result.stderr
        if "authorization grant is invalid" in output or "invalid_grant" in output:
            raise RuntimeError("SSL.com rechazo el acceso (invalid_grant). Revisar ES_USERNAME/ES_PASSWORD o el estado de la cuenta; no se ha firmado.")
        if "invalid otp" in output.lower():
            raise RuntimeError("SSL.com rechazo el OTP. Revisar ES_TOTP_SECRET para este certificado.")
        for code in ("invalid_request", "invalid_client", "invalid_token", "access_denied", "invalid_credential", "key status is disabled"):
            if code in output.lower():
                raise RuntimeError("SSL.com devolvio: " + code)
        if result.returncode or any(word in output for word in ("Error:", "Exception", "Missing required", "Unmatched argument")):
            detail = next((line for line in output.splitlines() if line.startswith("Error:")),
                          "CodeSignTool fallo con codigo " + str(result.returncode))
            for name in ("ES_USERNAME", "ES_PASSWORD", "CREDENTIAL_ID", "ES_TOTP_SECRET"):
                if os.environ.get(name):
                    detail = detail.replace(os.environ[name], "[oculto]")
            raise RuntimeError(detail[:400])
        expected = "Code signed successfully" if signing else "ADVISING TECHNOLOGY S.A.S." if info else "Credential ID(s):"
        if expected not in output:
            raise RuntimeError("No se pudo confirmar la firma o la consulta de credenciales de SSL.com.")
        if not signing and not info and os.environ["CREDENTIAL_ID"] not in output:
            raise RuntimeError("El acceso a SSL.com funciona, pero CREDENTIAL_ID no pertenece a las credenciales disponibles para esta cuenta.")
        print("Firma completada." if signing else "Acceso a SSL.com y CREDENTIAL_ID comprobados. No se ha solicitado una firma.")
    finally:
        shutil.rmtree(root / "logs", ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print("::error::" + str(error))
        sys.exit(1)
    except Exception:
        # Network/process exceptions can include arguments; do not dump them.
        print("::error::No se pudo ejecutar la comprobacion/firma de SSL.com.")
        sys.exit(1)

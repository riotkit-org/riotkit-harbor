from .apply import DeploymentTask
from .apply import CreateExampleDeploymentFileTask
from .syncfiles import UpdateFilesTask
from .vagrant import ManageVagrantTask
from .vault import EncryptVaultTask
from .vault import EnvEncryptTask
from .vault import EditVaultTask
from .ssh import SSHTask


def imports() -> list:
    return [
        DeploymentTask(),
        SSHTask(),
        CreateExampleDeploymentFileTask(),
        UpdateFilesTask(),
        ManageVagrantTask(),
        EncryptVaultTask(),
        EnvEncryptTask(),
        EditVaultTask()
    ]

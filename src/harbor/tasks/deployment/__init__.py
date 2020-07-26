from .apply import DeploymentTask
from .apply import CreateExampleDeploymentFileTask
from .syncfiles import UpdateFilesTask
from .vagrant import ManageVagrantTask
from .vault import EncryptVaultTask
from .vault import EnvEncryptTask
from .vault import EditVaultTask


def imports() -> list:
    return [
        DeploymentTask(),
        CreateExampleDeploymentFileTask(),
        UpdateFilesTask(),
        ManageVagrantTask(),
        EncryptVaultTask(),
        EnvEncryptTask(),
        EditVaultTask()
    ]

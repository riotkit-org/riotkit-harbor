import os
from rkd.syntax import TaskDeclaration
from rkd import main as rkd_main
from rkd.standardlib.env import GetEnvTask
from rkd.standardlib.env import SetEnvTask
from .tasks.diagnostic import ListContainersTask
from .tasks.running import StartTask
from .tasks.running import UpgradeTask
from .tasks.running import StopTask
from .tasks.running import StopAndRemoveTask
from .tasks.running import RestartTask
from .tasks.running import PullTask
from .tasks.service import LogsTask
from .tasks.service import AnalyzeServiceTask
from .tasks.service import InspectContainerTask
from .tasks.service import ExecTask
from .tasks.service import ServiceRemoveTask
from .tasks.service import ServiceUpTask
from .tasks.service import ServiceStopTask
from .tasks.service import WaitForServiceTask
from .tasks.listing import ListDefinedServices
from .tasks.deployment import DeploymentTask
from .tasks.deployment import UpdateFilesTask
from .tasks.deployment import CreateExampleDeploymentFileTask
from .tasks.deployment import ManageVagrantTask
from .tasks.deployment import EditVaultTask
from .tasks.deployment import EncryptVaultTask
from .tasks.deployment import EnvEncryptTask
from .tasks.diagnostic import DumpComposeArguments
from .tasks.diagnostic import DumpComposeConfigTask
from .tasks.gateway import ReloadGatewayTask
from .tasks.gateway import ShowSSLStatusTask
from .tasks.gateway import ForceReloadSSLTask
from .tasks.configsmanagement import ListConfigsTask
from .tasks.configsmanagement import EnableConfigTask
from .tasks.configsmanagement import DisableConfigTask
from .tasks.maintenance import MaintenanceOnTask
from .tasks.maintenance import MaintenanceOffTask
from .tasks.repositories import FetchRepositoryTask
from .tasks.repositories import SetPermissionsForWritableDirectoriesTask
from .tasks.repositories import ListRepositoriesTask
from .tasks.repositories import FetchAllRepositories
from .tasks.structure import CreateHarborStructureTask


def imports():
    return [
        TaskDeclaration(ListContainersTask()),
        TaskDeclaration(StartTask()),
        TaskDeclaration(UpgradeTask()),
        TaskDeclaration(StopTask()),
        TaskDeclaration(StopAndRemoveTask()),
        TaskDeclaration(ListDefinedServices()),
        TaskDeclaration(ServiceUpTask()),
        TaskDeclaration(ServiceStopTask()),
        TaskDeclaration(WaitForServiceTask()),
        TaskDeclaration(ServiceRemoveTask()),
        TaskDeclaration(ExecTask()),
        TaskDeclaration(LogsTask()),
        TaskDeclaration(AnalyzeServiceTask()),
        TaskDeclaration(InspectContainerTask()),
        TaskDeclaration(PullTask()),
        TaskDeclaration(RestartTask()),
        TaskDeclaration(ListConfigsTask()),
        TaskDeclaration(EnableConfigTask()),
        TaskDeclaration(DisableConfigTask()),
        TaskDeclaration(DumpComposeArguments()),
        TaskDeclaration(DumpComposeConfigTask()),

        # production-related
        TaskDeclaration(ReloadGatewayTask()),
        TaskDeclaration(ShowSSLStatusTask()),
        TaskDeclaration(ForceReloadSSLTask()),
        TaskDeclaration(MaintenanceOnTask()),
        TaskDeclaration(MaintenanceOffTask()),
        TaskDeclaration(DeploymentTask()),
        TaskDeclaration(UpdateFilesTask()),
        TaskDeclaration(CreateExampleDeploymentFileTask()),
        TaskDeclaration(ManageVagrantTask()),
        TaskDeclaration(EditVaultTask()),
        TaskDeclaration(EncryptVaultTask()),
        TaskDeclaration(EnvEncryptTask()),

        # git
        TaskDeclaration(FetchRepositoryTask()),
        TaskDeclaration(FetchAllRepositories()),
        TaskDeclaration(SetPermissionsForWritableDirectoriesTask()),
        TaskDeclaration(ListRepositoriesTask()),

        TaskDeclaration(CreateHarborStructureTask()),
        TaskDeclaration(GetEnvTask()),
        TaskDeclaration(SetEnvTask())
    ]


def env_or_default(env_name: str, default: str):
    return os.environ[env_name] if env_name in os.environ else default


def main():
    os.environ['RKD_PATH'] = os.path.dirname(os.path.realpath(__file__)) + '/internal:' + os.getenv('RKD_PATH', '')
    os.environ['RKD_WHITELIST_GROUPS'] = env_or_default('RKD_WHITELIST_GROUPS', ':env,:harbor,')
    os.environ['RKD_ALIAS_GROUPS'] = env_or_default('RKD_ALIAS_GROUPS', '->:harbor')
    os.environ['RKD_UI'] = env_or_default('RKD_UI', 'false')
    rkd_main()


if __name__ == '__main__':
    main()

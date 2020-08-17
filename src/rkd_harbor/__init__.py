import os
from rkd.api.syntax import TaskDeclaration
from rkd.api.syntax import TaskAliasDeclaration
from rkd import main as rkd_main
from rkd.standardlib.env import GetEnvTask
from rkd.standardlib.env import SetEnvTask
from rkd.standardlib.jinja import RenderDirectoryTask
from rkd.standardlib.jinja import FileRendererTask
from rkd_cooperative.tasks import CooperativeSyncTask
from rkd_cooperative.tasks import CooperativeInstallTask
from rkd_cooperative.tasks import CooperativeSnippetWizardTask
from rkd_cooperative.tasks import CooperativeSnippetInstallTask
from rkd import RiotKitDoApplication
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
from .tasks.service import GetContainerNameTask
from .tasks.service import ServiceUpTask
from .tasks.service import ServiceStopTask
from .tasks.service import WaitForServiceTask
from .tasks.listing import ListDefinedServices
from .tasks.deployment.apply import DeploymentTask
from .tasks.deployment.syncfiles import UpdateFilesTask
from .tasks.deployment.apply import CreateExampleDeploymentFileTask
from .tasks.deployment.vagrant import ManageVagrantTask
from .tasks.deployment.vault import EditVaultTask
from .tasks.deployment.vault import EncryptVaultTask
from .tasks.deployment.vault import EnvEncryptTask
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
        TaskDeclaration(GetContainerNameTask()),
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

        TaskDeclaration(CooperativeSyncTask()),
        TaskDeclaration(CooperativeInstallTask()),
        TaskDeclaration(CreateHarborStructureTask()),
        TaskDeclaration(CooperativeSnippetWizardTask()),
        TaskDeclaration(CooperativeSnippetInstallTask()),
        TaskDeclaration(GetEnvTask()),
        TaskDeclaration(SetEnvTask()),
        TaskDeclaration(FileRendererTask()),
        TaskDeclaration(RenderDirectoryTask()),

        # templates
        TaskAliasDeclaration(':harbor:templates:render',
                             [
                                 ':j2:directory-to-directory',
                                 '--source=containers/templates',
                                 '--target=data/templates'
                             ],
                             description='Render templates stored in containers/templates/source ' +
                                         'into containers/templates/compiled')
    ]


def env_or_default(env_name: str, default: str):
    return os.environ[env_name] if env_name in os.environ else default


def main():
    RiotKitDoApplication.load_environment()

    os.environ['RKD_PATH'] = os.path.dirname(os.path.realpath(__file__)) + '/internal:' + os.getenv('RKD_PATH', '')
    os.environ['RKD_WHITELIST_GROUPS'] = env_or_default('RKD_WHITELIST_GROUPS', ':env,:harbor,')
    os.environ['RKD_ALIAS_GROUPS'] = env_or_default('RKD_ALIAS_GROUPS', '->:harbor')
    os.environ['RKD_UI'] = env_or_default('RKD_UI', 'false')
    os.environ['COOP_REPOSITORIES'] = env_or_default(
        'COOP_REPOSITORIES', 'https://github.com/riotkit-org/harbor-snippet-cooperative')
    rkd_main()


if __name__ == '__main__':
    main()

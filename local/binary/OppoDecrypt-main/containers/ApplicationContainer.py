from dependency_injector import containers, providers

from core.models import CpuSupportEnum
from extractors import OfpQualcommExtractor, MtkExtractor, OpsExtractor, SparseExtractor, SuperImgExtractor
from services import ExtractService, LoguruLoggingService

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'

OFP_PREFIX = "ofp"
OPS_PREFIX = "ops"


class ApplicationContainer(containers.DeclarativeContainer):
    configuration = providers.Configuration()

    logging = providers.Singleton(
        LoguruLoggingService,
        configuration=configuration.log
    )

    extract_service = providers.Factory(
        ExtractService,
        extractors=providers.Dict({
            f"{OFP_PREFIX}_{CpuSupportEnum.QC.value}": providers.Factory(
                OfpQualcommExtractor,
                configuration=configuration.extractors.ofp_qualcomm,
                logger=logging
            ),
            f"{OFP_PREFIX}_{CpuSupportEnum.MTK.value}": providers.Factory(
                MtkExtractor,
                configuration=configuration.extractors.ofp_mtk,
                logger=logging
            ),

            f"{OPS_PREFIX}_{CpuSupportEnum.QC.value}": providers.Factory(
                OpsExtractor,
                configuration=configuration.extractors.ops,
                logger=logging
            ),
            f"{OPS_PREFIX}_{CpuSupportEnum.MTK.value}": providers.Factory(
                OpsExtractor,
                configuration=configuration.extractors.ops,
                logger=logging
            ),
            "sparse": providers.Factory(
                SparseExtractor,
                logger=logging
            ),
            "super": providers.Factory(
                SuperImgExtractor,
                logger=logging
            )

        }),
        logger=logging
    )

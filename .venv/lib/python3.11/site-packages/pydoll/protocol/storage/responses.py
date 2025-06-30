from typing import TypedDict

from pydoll.protocol.network.types import Cookie
from pydoll.protocol.storage.types import (
    RelatedWebsiteSet,
    SharedStorageEntry,
    SharedStorageMetadata,
    TrustToken,
    UsageForType,
)


class GetCookiesResultDict(TypedDict):
    cookies: list[Cookie]


class GetStorageKeyForFrameResultDict(TypedDict):
    storageKey: str


class GetUsageAndQuotaResultDict(TypedDict):
    usage: float
    quota: float
    overrideActive: bool
    usageBreakdown: list[UsageForType]


class ClearTrustTokensResultDict(TypedDict):
    didDeleteTokens: bool


class GetAffectedUrlsForThirdPartyCookieMetadataResultDict(TypedDict):
    matchedUrls: list[str]


class GetInterestGroupDetailsResultDict(TypedDict):
    details: dict


class GetRelatedWebsiteSetsResultDict(TypedDict):
    sets: list[RelatedWebsiteSet]


class GetSharedStorageEntriesResultDict(TypedDict):
    entries: list[SharedStorageEntry]


class GetSharedStorageMetadataResultDict(TypedDict):
    metadata: SharedStorageMetadata


class GetTrustTokensResultDict(TypedDict):
    tokens: list[TrustToken]


class RunBounceTrackingMitigationsResultDict(TypedDict):
    deletedSites: list[str]


class SendPendingAttributionReportsResultDict(TypedDict):
    numSent: int


class GetCookiesResponse(TypedDict):
    result: GetCookiesResultDict


class GetStorageKeyForFrameResponse(TypedDict):
    result: GetStorageKeyForFrameResultDict


class GetUsageAndQuotaResponse(TypedDict):
    result: GetUsageAndQuotaResultDict


class ClearTrustTokensResponse(TypedDict):
    result: ClearTrustTokensResultDict


class GetAffectedUrlsForThirdPartyCookieMetadataResponse(TypedDict):
    result: GetAffectedUrlsForThirdPartyCookieMetadataResultDict


class GetInterestGroupDetailsResponse(TypedDict):
    result: GetInterestGroupDetailsResultDict


class GetRelatedWebsiteSetsResponse(TypedDict):
    result: GetRelatedWebsiteSetsResultDict


class GetSharedStorageEntriesResponse(TypedDict):
    result: GetSharedStorageEntriesResultDict


class GetSharedStorageMetadataResponse(TypedDict):
    result: GetSharedStorageMetadataResultDict


class GetTrustTokensResponse(TypedDict):
    result: GetTrustTokensResultDict


class RunBounceTrackingMitigationsResponse(TypedDict):
    result: RunBounceTrackingMitigationsResultDict


class SendPendingAttributionReportsResponse(TypedDict):
    result: SendPendingAttributionReportsResultDict

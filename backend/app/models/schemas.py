from pydantic import BaseModel


class DonationRequest(BaseModel):
    donor_name: str
    amount: float


class DonationResponse(BaseModel):
    success: bool
    transaction_hash: str = None
    message: str
    donor_name: str
    amount: float = 0.0


class CampaignInfo(BaseModel):
    title: str
    description: str
    goal: float
    total_raised: float
    progress_percentage: float
    is_active: bool
    donors_count: int
    created_at: str


class DonationRecord(BaseModel):
    donor_name: str
    amount: float
    transaction_hash: str
    timestamp: str
    memo: str


class TopDonor(BaseModel):
    donor_name: str
    total: float
    count: int
    first_donation: str


class TopDonorsResponse(BaseModel):
    top_donors: list[TopDonor]
    total_unique_donors: int

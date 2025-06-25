# app/Models/campaign_models.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, Numeric, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.Models.base import Base

class Status(Base):
    __tablename__ = 'statuses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    model = Column(String(50), nullable=False)  # Where it's used (e.g. "list_member", "outreach")
    name = Column(String(50), nullable=False)   # e.g. "discovered", "assigned_to_ai", "responded"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    list_members = relationship("CampaignListMember", back_populates="status")
    outreach_statuses = relationship("InfluencerOutreach", foreign_keys="InfluencerOutreach.message_status_id")
    
class MessageChannel(Base):
    __tablename__ = 'message_channels'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), nullable=False)  # Full name of the channel (e.g. "Direct Message")
    shortname = Column(String(20), nullable=False)  # Abbreviation (e.g. "DM", "Story")
    description = Column(Text, nullable=True)  # Optional details or internal notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    outreach_channels = relationship("InfluencerOutreach", back_populates="message_channel")

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)  # Agent's display name
    platform_id = Column(UUID(as_uuid=True), ForeignKey('platforms.id', ondelete='CASCADE'), nullable=False)  # FK -> platforms.id (e.g. Instagram, WhatsApp)
    credentials = Column(JSONB, nullable=True)  # Serialized credentials (e.g. cookies, tokens)
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # FK -> users.id (User who will handle manual fallback)
    is_available = Column(Boolean, nullable=False, default=True)  # Whether agent is available for assignment
    current_assignment_id = Column(UUID(as_uuid=True), ForeignKey('list_assignments.id', ondelete='SET NULL'), nullable=True)  # FK -> list_assignments.id. Ongoing assignment.
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=True)  # New field - agent status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    platform = relationship("Platform", back_populates="agents")  # This should match the Platform.agents relationship
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])
    current_assignment = relationship("ListAssignment", foreign_keys=[current_assignment_id])
    assignments = relationship("ListAssignment", back_populates="agent", foreign_keys="ListAssignment.agent_id")
    status = relationship("Status", foreign_keys=[status_id])  # New relationship

class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(150), nullable=False)

    brand_name = Column(String(150), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    audience_age_group = Column(String(50), nullable=True)
    budget = Column(Numeric(10, 2), nullable=True)
    currency_code = Column(String(3), nullable=True)
    
    # Status field
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=True)
    
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    
    # Field to control default filters application
    default_filters = Column(Boolean, nullable=False, default=True)
    
    # Soft delete fields
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="campaigns")
    creator = relationship("User", foreign_keys=[created_by])
    deleter = relationship("User", foreign_keys=[deleted_by])  # New relationship for who deleted
    category = relationship("Category", foreign_keys=[category_id])
    status = relationship("Status", foreign_keys=[status_id])
    campaign_lists = relationship("CampaignList", back_populates="campaign", cascade="all, delete-orphan")
    message_templates = relationship("MessageTemplate", back_populates="campaign", cascade="all, delete-orphan")

    @property
    def all_list_assignments(self):
        """Get all list assignments for this campaign through campaign lists"""
        assignments = []
        for campaign_list in self.campaign_lists:
            assignments.extend(campaign_list.assignments)
        return assignments
    
class CampaignList(Base):
    __tablename__ = 'campaign_lists'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    message_template_id = Column(UUID(as_uuid=True), ForeignKey('message_templates.id', ondelete='SET NULL'), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    notes = Column(Text, nullable=True)  # New field before created_at
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_lists")  # This should match the renamed relationship in Campaign model
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("CampaignListMember", back_populates="list", cascade="all, delete-orphan")
    assignments = relationship("ListAssignment", back_populates="list", cascade="all, delete-orphan")
    outreach_records = relationship("InfluencerOutreach", back_populates="list")  # This is fine if we keep "InfluencerOutreach" name
    message_template = relationship("MessageTemplate")
    

class ListAssignment(Base):
    __tablename__ = 'list_assignments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    list_id = Column(UUID(as_uuid=True), ForeignKey('campaign_lists.id', ondelete='CASCADE'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    list = relationship("CampaignList", back_populates="assignments")
    agent = relationship("Agent", back_populates="assignments", foreign_keys=[agent_id])
    outreach_records = relationship("InfluencerOutreach", back_populates="assignment")
    status = relationship("Status")

class InfluencerOutreach(Base):
    __tablename__ = 'influencer_outreach'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Keep influencer_id for backward compatibility
    influencer_id = Column(UUID(as_uuid=True), ForeignKey('influencers.id', ondelete='CASCADE'), nullable=True)
    # Add social_account_id
    social_account_id = Column(UUID(as_uuid=True), ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=False)
    list_id = Column(UUID(as_uuid=True), ForeignKey('campaign_lists.id', ondelete='CASCADE'), nullable=False)
    list_member_id = Column(UUID(as_uuid=True), ForeignKey('campaign_list_members.id', ondelete='CASCADE'), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey('list_assignments.id', ondelete='SET NULL'), nullable=True)
    message_channel_id = Column(UUID(as_uuid=True), ForeignKey('message_channels.id', ondelete='SET NULL'), nullable=True)
    message_status_id = Column(UUID(as_uuid=True), ForeignKey('statuses.id', ondelete='SET NULL'), nullable=True)
    message_sent_at = Column(DateTime, nullable=True)
    error_code = Column(String(20), nullable=True)
    error_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    influencer = relationship("Influencer")
    social_account = relationship("SocialAccount", back_populates="outreach_records", overlaps="outreach_records")
    list = relationship("CampaignList", back_populates="outreach_records")
    list_member = relationship("CampaignListMember", back_populates="outreach_records")
    assignment = relationship("ListAssignment", back_populates="outreach_records")
    message_channel = relationship("MessageChannel", back_populates="outreach_channels")
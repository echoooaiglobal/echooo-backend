# app/Models/results.py

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, BigInteger, Numeric, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.Models.base import Base

class Result(Base):
    __tablename__ = 'results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    user_ig_id = Column(String(255), nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    influencer_username = Column(String(255), nullable=False, index=True)
    profile_pic_url = Column(Text, nullable=True)
    post_id = Column(String(255), nullable=True, index=True)
    title = Column(Text, nullable=True)
    views_count = Column(BigInteger, nullable=True)
    likes_count = Column(BigInteger, nullable=True)
    plays_count = Column(BigInteger, nullable=True)
    comments_count = Column(Integer, nullable=True)
    media_preview = Column(Text, nullable=True)
    duration = Column(Numeric(10, 2), nullable=True)  # Duration with decimal support (e.g., 30.5 seconds)
    thumbnail = Column(Text, nullable=True)
    post_created_at = Column(DateTime(timezone=True), nullable=True)
    post_result_obj = Column(JSONB, nullable=True)  # Store complete post object as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", foreign_keys=[campaign_id])
    
    __table_args__ = (
        # Campaign-based queries (very common)
        Index('ix_results_campaign_id', 'campaign_id'),
        
        # Analytics and reporting queries
        Index('ix_results_views_count', 'views_count'),
        Index('ix_results_likes_count', 'likes_count'),
        Index('ix_results_comments_count', 'comments_count'),
        Index('ix_results_plays_count', 'plays_count'),
        
        # Date-based filtering and sorting
        Index('ix_results_post_created_at', 'post_created_at'),
        Index('ix_results_created_at', 'created_at'),
        Index('ix_results_updated_at', 'updated_at'),
        
        # Composite indexes for common query patterns
        Index('ix_results_campaign_username', 'campaign_id', 'influencer_username'),
        Index('ix_results_campaign_post_date', 'campaign_id', 'post_created_at'),
        Index('ix_results_username_post_date', 'influencer_username', 'post_created_at'),
        
        # Performance analytics queries
        Index('ix_results_campaign_views', 'campaign_id', 'views_count'),
        Index('ix_results_campaign_likes', 'campaign_id', 'likes_count'),
        
        # Descending indexes for "top performers" queries
        Index('ix_results_views_desc', 'views_count', postgresql_ops={'views_count': 'DESC'}),
        Index('ix_results_likes_desc', 'likes_count', postgresql_ops={'likes_count': 'DESC'}),
    )
    
    def __repr__(self):
        return f"<Result(id={self.id}, campaign_id={self.campaign_id}, influencer_username='{self.influencer_username}', post_id='{self.post_id}')>"
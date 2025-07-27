# app/Models/currencies.py
# class Currency(Base):
#     __tablename__ = 'currencies'
    
#     code = Column(String(3), primary_key=True)  # USD, EUR, PKR, etc.
#     name = Column(String(50), nullable=False)   # US Dollar, Euro, Pakistani Rupee
#     symbol = Column(String(5), nullable=False)  # $, €, ₨
#     exchange_rate_to_usd = Column(Numeric(10, 6), nullable=True)
#     is_active = Column(Boolean, default=True)
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
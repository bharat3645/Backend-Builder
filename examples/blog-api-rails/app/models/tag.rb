class Tag < ApplicationRecord

  validates :color, length: { maximum: 7 }
  validates :name, presence: true, uniqueness: true, length: { maximum: 50 }
  validates :slug, uniqueness: true
end

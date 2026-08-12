class Tag < ApplicationRecord

  validates :name, presence: true, uniqueness: true, length: { maximum: 50 }
  validates :slug, uniqueness: true
  validates :color, length: { maximum: 7 }
end

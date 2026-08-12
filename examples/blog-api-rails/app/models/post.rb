class Post < ApplicationRecord
  belongs_to :author, class_name: 'User', optional: true
  has_and_belongs_to_many :tags, class_name: 'Tag', join_table: :posts_tags
  has_many :comments, class_name: 'Comment', foreign_key: 'post_id', dependent: :destroy

  validates :title, presence: true, length: { maximum: 200 }
  validates :slug, uniqueness: true
  validates :content, presence: true
  validates :status, inclusion: { in: %w[draft published archived] }
end

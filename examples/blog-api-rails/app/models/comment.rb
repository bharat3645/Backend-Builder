class Comment < ApplicationRecord
  belongs_to :author, class_name: 'User', optional: true
  belongs_to :parent, class_name: 'Comment', optional: true
  belongs_to :post, class_name: 'Post', optional: true
  has_many :comments, class_name: 'Comment', foreign_key: 'parent_id', dependent: :destroy

  validates :content, presence: true
end

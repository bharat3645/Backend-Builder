class User < ApplicationRecord
  has_many :posts, class_name: 'Post', foreign_key: 'author_id', dependent: :destroy
  has_many :comments, class_name: 'Comment', foreign_key: 'author_id', dependent: :destroy

  validates :email, presence: true, uniqueness: true, length: { maximum: 255 }
  validates :password, presence: true
  validates :first_name, length: { maximum: 100 }
  validates :last_name, length: { maximum: 100 }

  before_save do
    self.password = BCrypt::Password.create(password) if password_changed? && password.present?
  end
end

class CreatePosts < ActiveRecord::Migration[7.1]
  def change
    enable_extension 'pgcrypto' unless extension_enabled?('pgcrypto')

    create_table :posts, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :title, null: false, limit: 200
      t.string :slug, index: { unique: true }
      t.text :content, null: false
      t.text :excerpt
      t.string :status
      t.string :featured_image
      t.references :author, type: :uuid, foreign_key: { to_table: :users }, null: true
      t.datetime :published_at
      t.datetime :created_at
      t.datetime :updated_at
    end
  end
end

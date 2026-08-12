class CreatePosts < ActiveRecord::Migration[7.1]
  def change
    enable_extension 'pgcrypto' unless extension_enabled?('pgcrypto')

    create_table :posts, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.references :author, type: :uuid, foreign_key: { to_table: :users }, null: true
      t.text :content, null: false
      t.datetime :created_at
      t.text :excerpt
      t.string :featured_image
      t.datetime :published_at
      t.string :slug, index: { unique: true }
      t.string :status
      t.string :title, null: false, limit: 200
      t.datetime :updated_at
    end
  end
end

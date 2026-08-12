class CreateComments < ActiveRecord::Migration[7.1]
  def change
    enable_extension 'pgcrypto' unless extension_enabled?('pgcrypto')

    create_table :comments, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.references :author, type: :uuid, foreign_key: { to_table: :users }, null: true
      t.text :content, null: false
      t.datetime :created_at
      t.boolean :is_approved, default: false
      t.references :parent, type: :uuid, foreign_key: { to_table: :comments }, null: true
      t.references :post, type: :uuid, foreign_key: { to_table: :posts }, null: true
      t.datetime :updated_at
    end
  end
end

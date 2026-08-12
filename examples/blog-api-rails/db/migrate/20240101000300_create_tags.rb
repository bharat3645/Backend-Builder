class CreateTags < ActiveRecord::Migration[7.1]
  def change
    enable_extension 'pgcrypto' unless extension_enabled?('pgcrypto')

    create_table :tags, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :color, limit: 7
      t.datetime :created_at
      t.string :name, null: false, index: { unique: true }, limit: 50
      t.string :slug, index: { unique: true }
    end
  end
end

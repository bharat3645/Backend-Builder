class CreateUsers < ActiveRecord::Migration[7.1]
  def change
    enable_extension 'pgcrypto' unless extension_enabled?('pgcrypto')

    create_table :users, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :avatar
      t.text :bio
      t.datetime :created_at
      t.string :email, null: false, index: { unique: true }, limit: 255
      t.string :first_name, limit: 100
      t.boolean :is_active, default: true
      t.string :last_name, limit: 100
      t.string :password, null: false
      t.datetime :updated_at
    end
  end
end

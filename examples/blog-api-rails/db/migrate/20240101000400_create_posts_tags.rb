class CreatePostsTags < ActiveRecord::Migration[7.1]
  def change
    create_join_table :posts, :tags, table_name: :posts_tags do |t|
      t.column :post_id, :uuid
      t.column :tag_id, :uuid
      t.index [:post_id, :tag_id], name: 'index_posts_tags_on_both_ids'
    end
  end
end

module Api
  module V1
    class CommentsController < ApplicationController
      before_action :set_comment, only: [:show, :update, :destroy]

      def index
        render json: Comment.all
      end

      def show
        render json: @comment
      end

      def create
        comment = Comment.new(comment_params)
        if comment.save
          render json: comment, status: :created
        else
          render json: { errors: comment.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def update
        if @comment.update(comment_params)
          render json: @comment
        else
          render json: { errors: @comment.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def destroy
        @comment.destroy
        head :no_content
      end

      private

      def set_comment
        @comment = Comment.find(params[:id])
      end

      def comment_params
        params.require(:comment).permit(:author_id, :content, :created_at, :is_approved, :parent_id, :post_id, :updated_at)
      end
    end
  end
end

Rails.application.routes.draw do
  get '/health', to: proc { [200, {}, [{ status: 'healthy' }.to_json]] }

  namespace :api do
    namespace :v1 do
      resources :users
      resources :posts
      resources :comments
      resources :tags
    end
  end
end

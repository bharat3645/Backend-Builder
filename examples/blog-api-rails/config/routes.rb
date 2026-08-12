Rails.application.routes.draw do
  get '/health', to: proc { [200, {}, [{ status: 'healthy' }.to_json]] }

  namespace :api do
    namespace :v1 do
      resources :comments
      resources :posts
      resources :tags
      resources :users
    end
  end
end

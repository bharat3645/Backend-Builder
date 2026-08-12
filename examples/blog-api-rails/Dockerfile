FROM ruby:3.2-slim

RUN apt-get update -qq && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Gemfile ./
RUN bundle install
COPY . .

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["rails", "server", "-b", "0.0.0.0", "-p", "8000"]

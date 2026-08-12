package models

import (
	"time"
)

type Comment struct {
	AuthorID string `gorm:"type:uuid" json:"author_id"`
	Author *User `gorm:"foreignKey:AuthorID" json:"author,omitempty"`
	Content string `gorm:"not null" json:"content"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	IsApproved bool `gorm:"default:false" json:"is_approved"`
	ParentID string `gorm:"type:uuid" json:"parent_id"`
	Parent *Comment `gorm:"foreignKey:ParentID" json:"parent,omitempty"`
	PostID string `gorm:"type:uuid" json:"post_id"`
	Post *Post `gorm:"foreignKey:PostID" json:"post,omitempty"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

func (Comment) TableName() string { return "comments" }

type Post struct {
	AuthorID string `gorm:"type:uuid" json:"author_id"`
	Author *User `gorm:"foreignKey:AuthorID" json:"author,omitempty"`
	Content string `gorm:"not null" json:"content"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	Excerpt string `json:"excerpt"`
	FeaturedImage string `json:"featured_image"`
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	PublishedAt time.Time `json:"published_at"`
	Slug string `gorm:"unique" json:"slug"`
	Status string `json:"status"`
	Tags []Tag `gorm:"many2many:post_tags;" json:"tags,omitempty"`
	Title string `gorm:"not null;size:200" json:"title"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

func (Post) TableName() string { return "posts" }

type Tag struct {
	Color string `gorm:"size:7" json:"color"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	Name string `gorm:"unique;not null;size:50" json:"name"`
	Slug string `gorm:"unique" json:"slug"`
}

func (Tag) TableName() string { return "tags" }

type User struct {
	Avatar string `json:"avatar"`
	Bio string `json:"bio"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	Email string `gorm:"unique;not null;size:255" json:"email"`
	FirstName string `gorm:"size:100" json:"first_name"`
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	IsActive bool `gorm:"default:true" json:"is_active"`
	LastName string `gorm:"size:100" json:"last_name"`
	Password string `gorm:"not null" json:"password" json:"-"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

func (User) TableName() string { return "users" }


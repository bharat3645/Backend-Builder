package models

import (
	"time"
)

type User struct {
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	Email string `gorm:"unique;not null;size:255" json:"email"`
	Password string `gorm:"not null" json:"password" json:"-"`
	FirstName string `gorm:"size:100" json:"first_name"`
	LastName string `gorm:"size:100" json:"last_name"`
	Bio string `json:"bio"`
	Avatar string `json:"avatar"`
	IsActive bool `gorm:"default:true" json:"is_active"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

func (User) TableName() string { return "users" }

type Post struct {
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	Title string `gorm:"not null;size:200" json:"title"`
	Slug string `gorm:"unique" json:"slug"`
	Content string `gorm:"not null" json:"content"`
	Excerpt string `json:"excerpt"`
	Status string `json:"status"`
	FeaturedImage string `json:"featured_image"`
	AuthorID string `gorm:"type:uuid" json:"author_id"`
	Author *User `gorm:"foreignKey:AuthorID" json:"author,omitempty"`
	Tags []Tag `gorm:"many2many:post_tags;" json:"tags,omitempty"`
	PublishedAt time.Time `json:"published_at"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

func (Post) TableName() string { return "posts" }

type Comment struct {
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	Content string `gorm:"not null" json:"content"`
	AuthorID string `gorm:"type:uuid" json:"author_id"`
	Author *User `gorm:"foreignKey:AuthorID" json:"author,omitempty"`
	PostID string `gorm:"type:uuid" json:"post_id"`
	Post *Post `gorm:"foreignKey:PostID" json:"post,omitempty"`
	ParentID string `gorm:"type:uuid" json:"parent_id"`
	Parent *Comment `gorm:"foreignKey:ParentID" json:"parent,omitempty"`
	IsApproved bool `gorm:"default:false" json:"is_approved"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

func (Comment) TableName() string { return "comments" }

type Tag struct {
	Id string `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	Name string `gorm:"unique;not null;size:50" json:"name"`
	Slug string `gorm:"unique" json:"slug"`
	Color string `gorm:"size:7" json:"color"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
}

func (Tag) TableName() string { return "tags" }


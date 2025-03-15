"""
مدل‌های داده داخلی برای API توییتر

این ماژول، مدل‌های داده داخلی برای ساختارهای استاندارد داده‌های توییتر را تعریف می‌کند.
این مدل‌ها برای استاندارد‌سازی داده‌های دریافتی از API توییتر استفاده می‌شوند.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TwitterUserModel:
    """مدل داده کاربر توییتر"""
    
    user_id: str
    username: str
    twitter_id: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    tweets_count: int = 0
    profile_image_url: Optional[str] = None
    verified: bool = False
    created_at: Optional[datetime] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TwitterUserModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            twitter_id=data.get("twitter_id"),
            display_name=data.get("display_name"),
            bio=data.get("bio"),
            location=data.get("location"),
            followers_count=data.get("followers_count", 0),
            following_count=data.get("following_count", 0),
            tweets_count=data.get("tweets_count", 0),
            profile_image_url=data.get("profile_image_url"),
            verified=data.get("verified", False),
            created_at=data.get("created_at"),
            url=data.get("url"),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "twitter_id": self.twitter_id,
            "display_name": self.display_name,
            "bio": self.bio,
            "location": self.location,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "tweets_count": self.tweets_count,
            "profile_image_url": self.profile_image_url,
            "verified": self.verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "url": self.url,
            "metadata": self.metadata
        }


@dataclass
class HashtagModel:
    """مدل داده هشتگ"""
    
    text: str
    indices: Optional[List[int]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HashtagModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            text=data["text"],
            indices=data.get("indices")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "text": self.text,
            "indices": self.indices
        }


@dataclass
class MentionModel:
    """مدل داده منشن"""
    
    username: str
    user_id: Optional[str] = None
    indices: Optional[List[int]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MentionModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            username=data["username"],
            user_id=data.get("user_id"),
            indices=data.get("indices")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "username": self.username,
            "user_id": self.user_id,
            "indices": self.indices
        }


@dataclass
class UrlModel:
    """مدل داده URL در توییت"""
    
    url: str
    expanded_url: Optional[str] = None
    display_url: Optional[str] = None
    indices: Optional[List[int]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UrlModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            url=data["url"],
            expanded_url=data.get("expanded_url"),
            display_url=data.get("display_url"),
            indices=data.get("indices")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "url": self.url,
            "expanded_url": self.expanded_url,
            "display_url": self.display_url,
            "indices": self.indices
        }


@dataclass
class MediaModel:
    """مدل داده رسانه در توییت"""
    
    media_url: str
    type: str  # photo, video, animated_gif
    url: Optional[str] = None
    display_url: Optional[str] = None
    expanded_url: Optional[str] = None
    indices: Optional[List[int]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            media_url=data["media_url"],
            type=data["type"],
            url=data.get("url"),
            display_url=data.get("display_url"),
            expanded_url=data.get("expanded_url"),
            indices=data.get("indices")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "media_url": self.media_url,
            "type": self.type,
            "url": self.url,
            "display_url": self.display_url,
            "expanded_url": self.expanded_url,
            "indices": self.indices
        }


@dataclass
class EntitiesModel:
    """مدل داده موجودیت‌های توییت"""
    
    hashtags: List[HashtagModel] = field(default_factory=list)
    mentions: List[MentionModel] = field(default_factory=list)
    urls: List[UrlModel] = field(default_factory=list)
    media: List[MediaModel] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntitiesModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            hashtags=[HashtagModel.from_dict(h) for h in data.get("hashtags", [])],
            mentions=[MentionModel.from_dict(m) for m in data.get("mentions", [])],
            urls=[UrlModel.from_dict(u) for u in data.get("urls", [])],
            media=[MediaModel.from_dict(m) for m in data.get("media", [])]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "hashtags": [h.to_dict() for h in self.hashtags],
            "mentions": [m.to_dict() for m in self.mentions],
            "urls": [u.to_dict() for u in self.urls],
            "media": [m.to_dict() for m in self.media]
        }


@dataclass
class MetricsModel:
    """مدل داده آمار توییت"""
    
    likes_count: int = 0
    retweets_count: int = 0
    replies_count: int = 0
    quotes_count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricsModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            likes_count=data.get("likes_count", 0),
            retweets_count=data.get("retweets_count", 0),
            replies_count=data.get("replies_count", 0),
            quotes_count=data.get("quotes_count", 0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "likes_count": self.likes_count,
            "retweets_count": self.retweets_count,
            "replies_count": self.replies_count,
            "quotes_count": self.quotes_count
        }


@dataclass
class ReplyInfoModel:
    """مدل داده اطلاعات پاسخ توییت"""
    
    in_reply_to_tweet_id: Optional[str] = None
    in_reply_to_user_id: Optional[str] = None
    in_reply_to_username: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReplyInfoModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            in_reply_to_tweet_id=data.get("in_reply_to_tweet_id"),
            in_reply_to_user_id=data.get("in_reply_to_user_id"),
            in_reply_to_username=data.get("in_reply_to_username")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "in_reply_to_tweet_id": self.in_reply_to_tweet_id,
            "in_reply_to_user_id": self.in_reply_to_user_id,
            "in_reply_to_username": self.in_reply_to_username
        }


@dataclass
class TweetModel:
    """مدل داده توییت"""
    
    tweet_id: str
    text: str
    user: TwitterUserModel
    created_at: Optional[datetime] = None
    full_text: Optional[str] = None
    metrics: MetricsModel = field(default_factory=MetricsModel)
    entities: EntitiesModel = field(default_factory=EntitiesModel)
    reply_info: ReplyInfoModel = field(default_factory=ReplyInfoModel)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_entities: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TweetModel':
        """ایجاد نمونه کلاس از دیکشنری"""
        return cls(
            tweet_id=data["tweet_id"],
            text=data["text"],
            user=TwitterUserModel.from_dict(data["user"]),
            created_at=data.get("created_at"),
            full_text=data.get("full_text"),
            metrics=MetricsModel.from_dict(data.get("metrics", {})),
            entities=EntitiesModel.from_dict(data.get("entities", {})),
            reply_info=ReplyInfoModel.from_dict(data.get("reply_info", {})),
            metadata=data.get("metadata", {}),
            raw_entities=data.get("raw_entities", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل مدل به دیکشنری"""
        return {
            "tweet_id": self.tweet_id,
            "text": self.text,
            "user": self.user.to_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "full_text": self.full_text,
            "metrics": self.metrics.to_dict(),
            "entities": self.entities.to_dict(),
            "reply_info": self.reply_info.to_dict(),
            "metadata": self.metadata,
            "raw_entities": self.raw_entities
        }
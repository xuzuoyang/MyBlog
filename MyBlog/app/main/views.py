import logging, json, oss2
from enum import Enum
from .. import db
from . import main
from .forms import PostForm, CommentForm, MessageForm
from ..models import User, Post, Permission, Category, Comment, Tag, Tagging, Message
from ..decorators import permission_required, admin_required
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, current_app, request, abort, jsonify
from app.utils.file_manage import OssClient

logger = logging.getLogger('root')


@main.route('/')
def index():
    """The home page of the blog site.
    The showing content of every blog in this page is shortened to size of 256.
    """
    page = request.args.get('page', 1, type=int)
    logger.info('Visiting home at page {}.'.format(page))
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,
                                                                     per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    posts = []
    for item in pagination.items:
        post = {'id': item.id, 'title': item.title, 'timestamp': item.timestamp, 'last_edit': item.last_edit,
                'author': item.author.username, 'tagging': item.tagging, 'category': item.category.name}
        if len(item.body) > 256:
            post['body'] = item.body[:256] + '...'
        else:
            post['body'] = item.body + '...'
        posts.append(post)

    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('index.html', posts=posts, pagination=pagination, categories=categories, tags=tags)


@main.route('/about', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.COMMENT)
def about():
    """The about page which contains self introduction and message board.
    """
    messages = Message.query.order_by(Message.timestamp.desc())
    form = MessageForm()
    if form.validate_on_submit():
        logger.info('Submitting a new message.')
        title = form.title.data
        body = form.body.data
        author = current_user._get_current_object()
        message = Message(title=title, body=body, author=author)
        db.session.add(message)
        return redirect(url_for('main.about'))
    logger.info('Visiting about page.')
    return render_template('about.html', form=form, messages=messages)


@main.route('/search-category/<string:category>')
def search_category(category):
    """Search result page by category.
    """
    category = Category.query.filter_by(name=category.lower()).first_or_404()
    c_id = category.id

    page = request.args.get('page', 1, type=int)
    logger.info('Searching by category result at page {}.'.format(page))
    logger.info('Category id: {}.'.format(c_id))
    pagination = Post.query.filter_by(category_id=c_id).order_by(Post.timestamp.desc()).paginate(page,
                                                                     per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    posts = []
    for item in pagination.items:
        post = {'id': item.id, 'title': item.title, 'timestamp': item.timestamp,
                'author': item.author.username, 'tagging': item.tagging, 'category': item.category.name}
        if len(item.body) > 256:
            post['body'] = item.body[:256] + '...'
        else:
            post['body'] = item.body + '...'
        posts.append(post)

    return render_template('search.html', type='Category', category=category.name, posts=posts, pagination=pagination)


@main.route('/search-tag/<string:tag>')
def search_tag(tag):
    """Search result page by tag.
    """
    tag = Tag.query.filter_by(name=tag).first_or_404()
    t_id = tag.id

    page = request.args.get('page', 1, type=int)
    logger.info('Searching by tag result at page {}.'.format(page))
    logger.info('Tag id: {}.'.format(t_id))
    pagination = tag.tagging.order_by(Tagging.timestamp.desc()).paginate(page,
                                                                     per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    posts = []
    for item in pagination.items:
        item = item.post
        post = {'id': item.id, 'title': item.title, 'timestamp': item.timestamp,
                'author': item.author.username, 'tagging': item.tagging, 'category': item.category.name}
        if len(item.body) > 256:
            post['body'] = item.body[:256] + '...'
        else:
            post['body'] = item.body + '...'
        posts.append(post)

    return render_template('search.html', type='Tag', tag=tag.name, posts=posts, pagination=pagination)


@main.route('/blog/<blog_id>', methods=['GET', 'POST'])
def blog(blog_id):
    """Blog detail page.
    """
    post = Post.query.filter_by(id=blog_id).first()
    form = CommentForm()
    if current_user.can(Permission.COMMENT) and form.validate_on_submit():
        logger.info('Submitting a new comment.')
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, post=post)
        db.session.add(comment)
        return redirect(url_for('main.blog', blog_id=blog_id))
    logger.info('Visiting detail page of blog {}.'.format(blog_id))
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('blog.html', post=post, form=form, categories=categories, tags=tags)


@main.route('/thumb-up/<blog_id>', methods=['POST'])
@login_required
@permission_required(Permission.COMMENT)
def thumb_up(blog_id):
    """Interface of thumbing up a blog.
    """
    post = Post.query.filter_by(id=blog_id).first()
    post.thumb_up += 1
    logger.info('Thumbing up blog {} now.'.format(blog_id))
    logger.info('Blog {} has {} thumbs up now.'.format(blog_id, post.thumb_up))
    db.session.add(post)
    return jsonify(url=url_for('main.blog', blog_id=post.id))


@main.route('/manage-blog')
@login_required
@admin_required
def manage_blog():
    """Manage page of blogs.
    """
    page = request.args.get('page', 1, type=int)
    logger.info('Visiting blog manage page {}.'.format(page))
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,
                                                                     per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    posts = pagination.items
    return render_template('manage_blog.html', posts=posts, pagination=pagination)


@main.route('/manage-comment')
@login_required
@admin_required
def manage_comment():
    """Manage page of comments.
    """
    page = request.args.get('page', 1, type=int)
    logger.info('Visiting comment manage page {}.'.format(page))
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page,
                                                                     per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    comments = pagination.items
    return render_template('manage_comment.html', comments=comments, pagination=pagination)


@main.route('/manage-user')
@login_required
@admin_required
def manage_user():
    """Manage page of users.
    """
    page = request.args.get('page', 1, type=int)
    logger.info('Visiting user manage page {}.'.format(page))
    pagination = User.query.order_by(User.member_since.desc()).paginate(page,
                                                                     per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    users = pagination.items
    return render_template('manage_user.html', users=users, pagination=pagination)


@main.route('/write-blog', methods=['GET', 'POST'])
@login_required
@admin_required
def write_blog():
    """Writing new blog page.
    """
    if current_user.can(Permission.ADMINISTER) and request.method == 'POST':
        logger.info('Submitting a new blog.')
        form = request.form
        title, body = form.get('title', type=str, default=None), form.get('content', type=str, default=None)
        author = current_user._get_current_object()

        category = form.get('category', type=str, default=None)
        category = Category.query.filter_by(name=category).first().id

        post = Post(title=title, category_id=category, body=body, author=author)
        db.session.add(post)

        tags = form.get('tags', type=str, default=None).strip().split(',')
        # add new tag if not exist; tag current post
        if tags and len(tags[0]) > 0:
            for tag in tags:
                tag = tag.lower()
                if not Tag.query.filter_by(name=tag).first():
                    db.session.add(Tag(name=tag))
                    db.session.commit()
                t = Tag.query.filter_by(name=tag).first()
                t.tag_post(post)

        return jsonify({'url': url_for('main.manage_blog')})
    logger.info('Visiting write blog page.')
    url = url_for('main.write_blog')
    return render_template('write_blog.html', form=json.dumps({'url': url}))


@main.route('/edit/<blog_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blog(blog_id):
    """Edit blog page.
    """
    if not current_user.can(Permission.ADMINISTER):
        abort(403)
    post = Post.query.filter_by(id=blog_id).first_or_404()
    tags = list(map(lambda x: x.tag.name, post.tagging.all()))

    if request.method == 'POST':
        logger.info('Submitting changes of blog {}.'.format(blog_id))
        form = request.form
        post.title, post.body = form.get('title', type=str, default=None), form.get('content', type=str, default=None)
        post.author = current_user._get_current_object()

        category = form.get('category', type=str, default=None)
        category = Category.query.filter_by(name=category).first().id
        post.category_id = category

        # tags = request.values.get('tags', 5)
        # logging.warning('tags: %s' % tags)

        db.session.add(post)
        return jsonify({'url': url_for('main.manage_blog')})
    logger.info('Visiting edit page of blog {}.'.format(blog_id))
    url = url_for('main.edit_blog', blog_id=post.id)
    form = {'url': url, 'title': post.title, 'category': post.category_id, 'content': post.body, 'tags': tags}
    return render_template('write_blog.html', form=json.dumps(form))


@main.route('/delete/<blog_id>')
@login_required
@admin_required
def delete_blog(blog_id):
    """Delete blog interface.
    """
    if not current_user.can(Permission.ADMINISTER):
        abort(403)
    post = Post.query.filter_by(id=blog_id).first_or_404()
    db.session.delete(post)
    return redirect(url_for('main.manage_blog'))


@main.route('/upload_img', methods=['POST'])
@login_required
@admin_required
def upload_img():
    img = request.files['file']
    logging.info('Ready to upload image: {}'.format(img.filename))
    oc = OssClient()
    location = oc.upload_img(file=img)
    return jsonify(location=location)
